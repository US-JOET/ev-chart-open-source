"""
InfraChangeUploadStatus

Function run from a GitHub Action that will change the status of a specified upload to what has been
requested.  Generally used for an O&M process that will "reject" a previously approved module
upload.
"""
from datetime import datetime, UTC
from evchart_helper import aurora
from evchart_helper.custom_logging import LogEvent
from evchart_helper.database_tables import ModuleDataTables

import_metadata = ModuleDataTables["Metadata"].value

def handler(event, context):
    try:
        log = LogEvent(event, api="InfraChangeUploadStatus", action_type="READ")
        connection = aurora.get_connection()
        cursor = connection.cursor()
        upload_id = event.get('upload_id')
        status = event.get('submission_status')
        current_time = str(datetime.now(UTC))

        #Check module data tables for any submitted data
        update_upload_metadata(current_time, status, upload_id, cursor, log)
        connection.commit()

    except Exception as err:
        print(f"Error: {repr(err)}")
        raise

    finally:
        aurora.close_connection()
        print("Closed cursor and connection")

def update_upload_metadata(current_time, status, upload_id, cursor, log):
    update_upload_query = f"""
            UPDATE {import_metadata}
            SET updated_on = '{current_time}', submission_status = '{status}', updated_by = 'SYSTEM'
            WHERE upload_id = '{upload_id}'
            """
    cursor.execute(update_upload_query)
    log.log_successful_request(
            message=f"Updated upload {upload_id} to {status}", status_code=200
    )
