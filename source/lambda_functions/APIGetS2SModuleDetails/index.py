"""
APIGetS2SModuleDetails

This function returns the general metadata related to a module submission for the S2S process.
"""
import json

from evchart_helper.custom_exceptions import (
    EvChartAPIS2SError,
    EvChartDatabaseDynamoQueryError,
    EvChartDynamoConnectionError,
    EvChartInvalidAPIKey,
    EvChartJsonOutputError,
    EvChartLambdaConnectionError,
    EvChartMissingOrMalformedBodyError,
)
from evchart_helper import aurora
from evchart_helper.custom_logging import LogEvent
from evchart_helper.module_helper import (
    format_metadata,
    get_module_details,
    is_org_authorized_to_view_data,
    is_valid_upload_id,
)
from evchart_helper.s2s_helper import (
    check_valid_api_key,
    get_api_key_from_event,
    get_org_by_api_key,
)
from feature_toggle import feature_enablement_check
from feature_toggle.feature_enums import Feature


# Lambda that allows API user to retrieve module upload details
@feature_enablement_check(Feature.S2S)
def handler(event, _context):
    log_event = LogEvent(event=event, api="APIPostS2SImportModuleData", action_type="insert")
    log_event.log_info(event)

    # header should have api key we extract org_id from api key
    # body should have upload_id
    try:
        api_key = get_api_key_from_event(event)
        check_valid_api_key(api_key)
        org_id = get_org_by_api_key(api_key)
        log_event.log_debug(org_id)

        recipient_type = "sub-recipient"
        body = json.loads(event.get("body"))
        connection = aurora.get_connection()
        with connection.cursor() as cursor:
            validation_errors = validate_body(body, org_id, recipient_type, cursor)
            if len(validation_errors) > 0:
                error_list_string = ", ".join(validation_errors)
                raise EvChartMissingOrMalformedBodyError(
                    message=f"Errors found: {error_list_string}"
                )

            upload_id = body.get("upload_id")

            # retrieving module data
            module_details = get_module_details(upload_id, org_id, recipient_type, cursor)

            formated_module_details = module_details.copy()
            format_metadata(recipient_type, formated_module_details)
            return_body = format_response_body(formated_module_details)

    except (
        EvChartInvalidAPIKey,
        EvChartDynamoConnectionError,
        EvChartMissingOrMalformedBodyError,
        EvChartJsonOutputError,
        EvChartLambdaConnectionError,
        EvChartDatabaseDynamoQueryError,
        EvChartAPIS2SError,
    ) as e:
        log_event.log_custom_exception(
            message=e.message, status_code=e.status_code, log_level=e.log_level
        )
        return_obj = e.get_error_obj()
    else:

        return_obj = {
            "body": json.dumps(return_body),
            "headers": {"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"},
            "statusCode": 200,
        }

    return return_obj


def validate_body(body, org_id, recipient_type, cursor):
    error_list = []
    upload_id = body.get("upload_id")
    if upload_id:
        if not is_valid_upload_id(upload_id, cursor):
            error_list.append(f"Invalid upload_id: {upload_id}")

        if len(error_list) == 0:
            if not is_org_authorized_to_view_data(upload_id, org_id, recipient_type, cursor):
                error_list.append(
                    f"you are not permitted to view data associated with upload id: {upload_id}"
                )
    else:
        error_list.append("missing required field: upload_id")

    return error_list


# Uses formated metadata and removes items that user should not see eg. Ord_id
# see test for example of module_details
def format_response_body(module_details):
    formated_obj = {}
    detail = module_details[0]

    output_keys = [
        "direct_recipient",
        "upload_id",
        "module_id",
        "module_name",
        "module_frequency",
        "year",
        "quarter",
        "submission_status",
        "uploaded_on",
    ]

    value_exists_keys = ["comments"]

    try:
        for key in output_keys:
            if key == "submission_status":
                translated_status = format_submission_status(detail[key])
                formated_obj[key] = translated_status
            else:
                formated_obj[key] = detail[key]

        for key in value_exists_keys:
            if detail[key]:
                formated_obj[key] = detail[key]
    except KeyError as e:
        raise EvChartAPIS2SError(
            message=f"internal error during formating response: {repr(e)}"
        ) from e

    return formated_obj


def format_submission_status(status):
    formatted_status = ""
    match status.lower():
        case "processing":
            formatted_status = "Upload Draft"
        case "pending":
            formatted_status = "Pending Approval"
        case _:
            formatted_status = status.capitalize()

    return formatted_status
