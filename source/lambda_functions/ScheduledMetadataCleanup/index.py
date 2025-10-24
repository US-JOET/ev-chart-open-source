"""
ScheduledMetadataCleanup

A function run on a schedule that will clean up any stale module upload metadata (modules that were
expected to be uploaded but were not for any particular reason).
"""
from evchart_helper import aurora
from email_handler import trigger_email
from email_handler.email_enums import Email_Template
from email_handler.html_templates import upload_cleanup
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.api_helper import (
    get_org_info_dynamo,
    get_org_users,
    format_users,
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.custom_exceptions import (
    EvChartDatabaseAuroraQueryError,
    EvChartJsonOutputError,
)
import pandas as pd

import_metadata = ModuleDataTables["Metadata"].value

def handler(event, context):
    try:
        connection = aurora.get_connection()
        cursor = connection.cursor()
        log = LogEvent(event, api="ScheduledMetadataCleanup", action_type="Read")

        removable_upload_ids, uploads_df = get_removable_uploads(cursor, log)
        draftable_upload_ids = get_draftable_uploads(cursor, log)
        if removable_upload_ids:
            formatted_ids = tuple(removable_upload_ids) if (len(removable_upload_ids) > 1) else f'("{removable_upload_ids[0]}")'
            delete_failed_upload_metadata(cursor, formatted_ids, log)
            formatted_tables = format_removed_uploads_email_table(uploads_df)
            send_all_emails(formatted_tables)
        if draftable_upload_ids:
            formatted_ids = tuple(draftable_upload_ids) if (len(draftable_upload_ids) > 1) else f'("{draftable_upload_ids[0]}")'
            update_completed_upload_metadata(cursor, formatted_ids, log)

    except (
        EvChartDatabaseAuroraQueryError,
    ) as e:
        log.log_custom_exception(
            message=e.message, status_code=e.status_code, log_level=e.log_level
            )
    except Exception as e:
        print(f"Unknown Exception in ScheduleMetadata Cleanup: {repr(e)}")
        raise e

    else:
        connection.commit()
        log.log_successful_request(
            message=f"Succesfully removed {len(removable_upload_ids)} failed uploads, set {len(draftable_upload_ids)} to Draft", status_code=200
        )

    finally:
        aurora.close_connection()

#returns list of upload_ids for uploads that are without data and have been in proccessing for 3 or more hours
def get_removable_uploads(cursor, log):
    upload_ids = []
    get_uploads_query = f"""
        SELECT im.upload_id, im.org_id, im.parent_org, im.quarter, im.updated_on, im.year, im.module_id
        FROM {import_metadata} im
        WHERE im.submission_status = "Processing"
        AND im.updated_on <= DATE_SUB(NOW(), INTERVAL 3 HOUR)
        AND NOT EXISTS (SELECT 1 FROM {ModuleDataTables["Module2"].value} m2 WHERE im.upload_id = m2.upload_id)
        AND NOT EXISTS (SELECT 1 FROM {ModuleDataTables["Module3"].value} m3 WHERE im.upload_id = m3.upload_id)
        AND NOT EXISTS (SELECT 1 FROM {ModuleDataTables["Module4"].value} m4 WHERE im.upload_id = m4.upload_id)
        AND NOT EXISTS (SELECT 1 FROM {ModuleDataTables["Module5"].value} m5 WHERE im.upload_id = m5.upload_id)
        AND NOT EXISTS (SELECT 1 FROM {ModuleDataTables["Module6"].value} m6 WHERE im.upload_id = m6.upload_id)
        AND NOT EXISTS (SELECT 1 FROM {ModuleDataTables["Module7"].value} m7 WHERE im.upload_id = m7.upload_id)
        AND NOT EXISTS (SELECT 1 FROM {ModuleDataTables["Module8"].value} m8 WHERE im.upload_id = m8.upload_id)
        AND NOT EXISTS (SELECT 1 FROM {ModuleDataTables["Module9"].value} m9 WHERE im.upload_id = m9.upload_id)
    """
    try:
        cursor.execute(get_uploads_query)
    except Exception as e:
        raise EvChartDatabaseAuroraQueryError(message="Error in get_removable_uploads()", log_obj=log)

    row_data = cursor.fetchall()
    column_names = [column[0] for column in cursor.description]
    df = pd.DataFrame(row_data, columns=column_names)

    upload_ids = df['upload_id'].tolist()
    if upload_ids:
        log.log_successful_request(
                message=f"Number of removable uploads found: {len(upload_ids)} List of upload_ids:{upload_ids}", status_code=200
            )
    return upload_ids, df

def format_removed_uploads_email_table(uploads_df):
    table_string = str(upload_cleanup.table_item)
    combined_table = {}
    for org_id in uploads_df['org_id'].unique():
        combined_table[org_id] = ""
        filtered_df = uploads_df[uploads_df['org_id'] == org_id]
        for _,row in filtered_df.iterrows():
            try:
                dr_org_id = row.parent_org
                dr_name = get_org_info_dynamo(dr_org_id).get("name")
            except KeyError:
                dr_name = 'N/A'
            new_table_row = table_string
            combined_table[org_id] += new_table_row.format(
                upload_id=row.upload_id,
                module_number=row.module_id,
                reporting_year=row.year,
                quarter=row.quarter,
                dr_name=dr_name,
                updated_on=row.updated_on
            )
    return combined_table

def send_all_emails(combined_table):
    try:
        email_values = {}
        email_values["email_type"] = Email_Template.UPLOAD_FAILED
        for org, table in combined_table.items():
            email_values["table"] = table
            org_users = get_org_users(org)
            formatted_users = format_users(org_users)
            for user in formatted_users:
                if user.get("status") == "Active" and user.get("role") == "Administrator":
                    email_values["first_name"] = user.get("first_name").strip()
                    email_values["email"] = user.get("email").strip()
                    trigger_email(email_values)
    except EvChartJsonOutputError as e:
        raise e
    except Exception as e:
        raise EvChartJsonOutputError(
            log_obj=None,
            message=f"Error formatting fields for email handler: {repr(e)}"
        ) from e


#returns list of upload_ids for uploads that are WITH data and have been in proccessing for 3 or more hours
def get_draftable_uploads(cursor, log):
    upload_ids = []
    get_uploads_query = f"""
        SELECT im.upload_id
        FROM {import_metadata} im
        WHERE im.submission_status = "Processing"
        AND im.updated_on <= DATE_SUB(NOW(), INTERVAL 3 HOUR)
        AND (EXISTS (SELECT 1 FROM {ModuleDataTables["Module2"].value} m2 WHERE im.upload_id = m2.upload_id)
        OR EXISTS (SELECT 1 FROM {ModuleDataTables["Module3"].value} m3 WHERE im.upload_id = m3.upload_id)
        OR EXISTS (SELECT 1 FROM {ModuleDataTables["Module4"].value} m4 WHERE im.upload_id = m4.upload_id)
        OR EXISTS (SELECT 1 FROM {ModuleDataTables["Module5"].value} m5 WHERE im.upload_id = m5.upload_id)
        OR EXISTS (SELECT 1 FROM {ModuleDataTables["Module6"].value} m6 WHERE im.upload_id = m6.upload_id)
        OR EXISTS (SELECT 1 FROM {ModuleDataTables["Module7"].value} m7 WHERE im.upload_id = m7.upload_id)
        OR EXISTS (SELECT 1 FROM {ModuleDataTables["Module8"].value} m8 WHERE im.upload_id = m8.upload_id)
        OR EXISTS (SELECT 1 FROM {ModuleDataTables["Module9"].value} m9 WHERE im.upload_id = m9.upload_id))
    """
    try:
        cursor.execute(get_uploads_query)
    except Exception as e:
        raise EvChartDatabaseAuroraQueryError(message="Error in get_draftable_uploads()", log_obj=log)

    upload_ids = [row[0] for row in cursor.fetchall()]
    if upload_ids:
        log.log_successful_request(
                message=f"Number of draftable uploads found: {len(upload_ids)} List of upload_ids:{upload_ids}", status_code=200
            )
    return upload_ids

def delete_failed_upload_metadata(cursor, upload_ids, log):
    delete_query = f"""
        DELETE
        FROM {import_metadata}
        WHERE upload_id IN {upload_ids}
    """
    try:
        cursor.execute(delete_query)
    except Exception as e:
        raise EvChartDatabaseAuroraQueryError(
            message="Error in delete_failed_upload_metadata()", log_obj=log
        )

def update_completed_upload_metadata(cursor, upload_ids, log):
    update_query = f"""
        UPDATE {import_metadata}
        SET submission_status = 'Draft'
        WHERE upload_id IN {upload_ids}
    """
    try:
        cursor.execute(update_query)
    except Exception as e:
        raise EvChartDatabaseAuroraQueryError(
            message="Error in update_completed_upload_to_draft()", log_obj=log
        )
