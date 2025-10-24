"""
schema_compliance.error_table

Holds the functions used to insert into the error table
"""

import json
import datetime
from dateutil import tz
from evchart_helper.api_helper import execute_query, get_org_info_dynamo
from evchart_helper.custom_exceptions import EvChartJsonOutputError
from evchart_helper.database_tables import ModuleDataTables

ev_error_data = ModuleDataTables["EvErrorData"].value

def error_table_insert(cursor, upload_id, module_id, org_id, dr_id, condition_list, df):
    """
        Returns True if data was successfully inserted into the ev_error_table
        NOTE: Only provide dr_id if org_id is an SR
    """
    query_data = {}

    #set upload_id, module_id, timestamp for all records going into error table
    query_data["upload_id"] = upload_id
    query_data["module_id"] = module_id
    query_data["timestamp"] = datetime.datetime.now(tz.gettz("UTC"))

    #setting row level errors
    for condition in condition_list:
        #sets general error info
        query_data["error_row"] = condition["error_row"]
        query_data["error_description"] = condition["error_description"]
        query_data["header_name"] = condition["header_name"]
        set_org_ids(query_data, org_id, dr_id)

        #sets row level errors: record, station_id, friendly dr_id, friendly sr_id
        if query_data["error_row"] is not None:
            set_record(query_data, condition, df)
            set_station_id(query_data, condition, df)

        #sets column level errors
        else:
            query_data["record"] = json.dumps({})
            query_data["station_id"] = None

        insert_query = f"""
            INSERT INTO {ev_error_data}
            (upload_id, module_id, timestamp, error_row, error_description, header_name, dr_org_friendly_id, sr_org_friendly_id, record, station_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        execute_query(
            query=insert_query,
            data=tuple(query_data.values()),
            cursor=cursor, message="Error thrown in schema_compliance.error_table error_table_insert(). "
        )
    return True


def set_record(query_data, condition_obj, df):
    """
        Convenience function that references the condition_obj to set the correct error record in
        query_data which will be the data used to insert into error table. The updated
        query_data dictionary is returned.
    """
    try:
        #get the error row and do a lookup on the df to get contents of record and store into a dict
        record = df.loc[condition_obj["error_row"]].to_dict()
        json_record = json.dumps(record, default=str)
        query_data["record"] = json_record
        return query_data

    except Exception as e:
        raise EvChartJsonOutputError(message=f"Error thrown inserting into error_table. Helper function: set_record(): {e}" )



def set_station_id(query_data, condition, df):
    """
        Convenience function that appends station_id into query_data which will be the data used to insert into error table.
        The updated query_data dictionary is returned.
    """
    try:
        error_row = condition["error_row"]
        station_id = df.loc[error_row]["station_id"]
        query_data["station_id"] = station_id
        return query_data

    except Exception as e:
        raise EvChartJsonOutputError(message=f"Error thrown inserting into error_table. Helper function: set_station(): {e}" )


def set_org_ids(query_data, org_id, dr_id=None):
    """
        Convenience function that appends dr_org_friendly_id and sr_org_friendly_id to query_data.
        The updated query_data dictionary is returned.
    """
    org_info = get_org_info_dynamo(org_id)
    recipient_type = org_info.get("recipient_type")

    if recipient_type == "direct-recipient":
        query_data["dr_org_friendly_id"] = org_info.get("org_friendly_id")
        query_data["sr_org_friendly_id"] = None

    elif recipient_type == "sub-recipient":
        dr_info = get_org_info_dynamo(dr_id)
        query_data["dr_org_friendly_id"] = dr_info.get("org_friendly_id")
        query_data["sr_org_friendly_id"] = org_info.get("org_friendly_id")

    return query_data