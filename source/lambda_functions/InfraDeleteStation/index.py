"""
InfraDeleteStation

[Deprecated, UI-capable] As part of a GitHub Action, delete and remove a registered station.
"""
import json
from evchart_helper import aurora
from evchart_helper.station_helper import remove_station
from evchart_helper.custom_exceptions import (
    EvChartDatabaseAuroraDuplicateItemError,
    EvChartDatabaseAuroraQueryError,
    EvChartMissingOrMalformedBodyError,
)

def handler(event, context):
    response = ""
    station_uuid = event.get('station_uuid')
    try:
        connection = aurora.get_connection()
        cursor = connection.cursor()
        remove_station(station_uuid, cursor)
        connection.commit()
    except EvChartDatabaseAuroraDuplicateItemError:
        response = ("!! Station has data, unable to delete!!")
    except EvChartMissingOrMalformedBodyError:
        response = (f"Station {station_uuid} does not exist!")
    except Exception as e:
        response = (f"Error thrown: {repr(e)}")
    else:
        response = "Station deleted!"

    finally:
        aurora.close_connection()

    return json.dumps(response)
