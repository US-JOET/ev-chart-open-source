"""
APIGetUploadOptions

Return the values to the frontend that are used for options to select when uploading module data.
"""
import json
from datetime import datetime, timezone

from database_central_config import DatabaseCentralConfig
from evchart_helper import aurora
from evchart_helper.api_helper import get_available_years
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError, EvChartDatabaseAuroraQueryError,
    EvChartDatabaseDynamoQueryError, EvChartUserNotAuthorizedError)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.session import SessionManager
from evchart_helper.user_helper import get_authorized_drs
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature


@SessionManager.check_session()
def handler(event, _context):
    connection = aurora.get_connection()
    todays_date = datetime.now(timezone.utc).date()
    with connection.cursor() as cursor:
        try:
            log_event = LogEvent(event, api="APIGetOrgUserData", action_type="Read")
            if log_event.is_auth_token_valid() is False:
                raise EvChartAuthorizationTokenInvalidError()

            features = FeatureToggleService().get_active_feature_toggles(log_event=log_event)

            token = log_event.get_auth_token()
            org_id = token["org_id"]
            org_type = token["recipient_type"]
            if org_type not in ["direct-recipient", "sub-recipient"]:
                raise EvChartUserNotAuthorizedError(message="User must be of valid recipient type")

            if Feature.DATABASE_CENTRAL_CONFIG in features:
                config = DatabaseCentralConfig()
                output = {
                    "modules_quarterly": {
                        module_id: config.module_display_name(module_id)
                        for module_id in config.quarterly_module_ids()
                    },
                    "modules_other": {
                        module_id: config.module_display_name(module_id)
                        for module_id in (
                            config.onetime_module_ids() +
                            config.annual_module_ids()
                        )
                    }
                }
            else:
                output = {}
                output["modules_quarterly"] = { "2": "Module 2: Charging Sessions", "3": "Module 3: Uptime", "4": "Module 4: Outages" }
                output["modules_other"] = { "5": "Module 5: Maintenance Costs",
                                        "6": "Module 6: Station Operator Identity",
                                        "7": "Module 7: Station Operator Program",
                                        "8": "Module 8: DER Information",
                                        "9": "Module 9: Capital and Installation Costs" }

            output["years"] = get_available_years(todays_date)
            output["type"] = ["one-time", "annual", "quarterly"]
            output["quarters"] = { "1": "Quarter 1 (Jan-Mar): Due 4/30",
                                "2": "Quarter 2 (Apr-Jun): Due 7/31",
                                "3": "Quarter 3 (Jul-Sep): Due 10/31",
                                "4": "Quarter 4 (Oct-Dec): Due 1/31" }

            if str(org_type) == "sub-recipient":
                dr_list = get_authorized_drs(
                    org_id,
                    cursor,
                    n_tier_enabled=Feature.N_TIER_ORGANIZATIONS in features
                )
                output["direct_recipients"] = dr_list


        except (EvChartAuthorizationTokenInvalidError,
                EvChartDatabaseDynamoQueryError,
                EvChartDatabaseAuroraQueryError,
                EvChartUserNotAuthorizedError
        ) as e:
            log_event.log_custom_exception(
                message=e.message,
                status_code=e.status_code,
                log_level=e.log_level
            )
            return_obj = e.get_error_obj()

        else:
            log_event.log_successful_request(
                message="Successfully returned upload options",
                status_code=200
            )
            return_obj = {
                'statusCode' : 200,
                'headers': { "Access-Control-Allow-Origin": "*" },
                'body': json.dumps(output)
            }

        finally:
            aurora.close_connection()

        return return_obj