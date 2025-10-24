"""
feature_toggle

A helper module that handles the definition and processing of the application feature toggles.
"""
import json
import logging
import os

from botocore.exceptions import ClientError, NoCredentialsError
from evchart_helper.boto3_manager import boto3_manager
from evchart_helper.custom_exceptions import EvChartFeatureStoreConnectionError
from evchart_helper.custom_logging import LogEvent
from feature_toggle.feature_enums import Feature, PseudoFeature


def feature_enablement_check(required_feature: Feature):
    """
    Decorator
    Parameter: Feature Enum
    Descirption: When used above a function if the Feature toggle is off it will return a
    403 error.  If toggle does not exist in the parameter store returns a 500
    otherwise just runs the function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                # args[0] for the event
                # func.__module__ = dir+file of function eg. APIPostUser.index
                module = func.__module__
                if '.index' in module:
                    module = module.replace('.index', '')
                log = LogEvent(args[0], api=f'{module}_feature_enablement_check', action_type="READ")
                feature_toggle_service = FeatureToggleService()
                feature = feature_toggle_service.get_feature_toggle_by_enum(
                    feature=required_feature,
                    log=log
                )
                return_obj = None
                if feature is None:
                    return_obj = {
                        "statusCode": 500,
                        "headers": {"Access-Control-Allow-Origin": "*"},
                        "body": json.dumps(
                            f"Feature Not Found: No feature found with the name {required_feature.value}"
                        ),
                    }
                else:
                    feature_is_active = feature
                    if feature_is_active == "False":
                        return_obj = {
                            "statusCode": 403,
                            "headers": {"Access-Control-Allow-Origin": "*"},
                            "body": json.dumps(
                                f"Error feature is disabled: Feature {required_feature.value} is currently disabled"
                            ),
                        }
            except EvChartFeatureStoreConnectionError as e:
                return_obj = e.get_error_obj()

            if return_obj is not None:
                logger = logging.getLogger()
                logger.info(return_obj)
                return return_obj
            return func(*args, **kwargs)

        return wrapper

    return decorator

# Class that provides access to feature toggle values
class FeatureToggleService:
    def __init__(self):
        self.ssm = boto3_manager.client("ssm")

    def get_all_feature_toggles(self, log: LogEvent):
        """
        Returns a list of feature toggles and their values
        Object is a list of {Name, Value}
        """
        sub_environment = os.environ.get("SUBENVIRONMENT")
        sub_environment_path = f"/{sub_environment}" if sub_environment else ""

        feature_path = f"/ev-chart/features{sub_environment_path}"
        try:
            parameter_list = []
            paginator = self.ssm.get_paginator('get_parameters_by_path')

            for page in paginator.paginate(Path=feature_path):
                parameter_list.extend(page.get("Parameters", []))

            # parameter_list = self.ssm.get_parameters_by_path(Path=feature_path)
        except NoCredentialsError as e:
            raise EvChartFeatureStoreConnectionError(operation="Get", log_obj= log) from e

        environment = sub_environment or os.environ.get("ENVIRONMENT")
        for pseudo_feature in PseudoFeature:
            try:
                feature_name = Feature[pseudo_feature.name].value

                if environment in pseudo_feature.value:
                    found_param = False
                    for parameter in parameter_list:
                        if parameter["Name"].split("/")[-1] == feature_name:
                            found_param = True

                            parameter["Value"] = "True"
                            break

                    if not found_param:
                        parameter_list.extend([{
                            "Name": feature_name,
                            "Value": "True",
                        }])

            except KeyError:
                # Silently fail and move on.
                pass

        return_value = [{
            "Name": parameter["Name"].split("/")[-1],
            "Value": {"true": True}.get(parameter["Value"].lower(), False)
            } for parameter in parameter_list]
        return return_value

    def get_feature_toggle_by_name(self, name: str, log: LogEvent):
        """
        Parameter : name as a string this is the name of the feature toggle
        returns the string value of the parameter should be True or False
        """
        sub_environment = os.environ.get("SUBENVIRONMENT")
        sub_environment_path = f"/{sub_environment}" if sub_environment else ""

        feature_path = f"/ev-chart/features{sub_environment_path}/{name}"

        environment = sub_environment or os.environ.get("ENVIRONMENT")

        try:
            identifier = Feature(name).name
            if (
                identifier in PseudoFeature.__members__
                and environment in PseudoFeature[identifier].value
            ):
                return "True"

        except ValueError:
            # Silently fail and move on.
            pass

        try:
            parameter = self.ssm.get_parameter(Name=feature_path)
            if parameter is None:
                parameter["Parameter"] = None
        except NoCredentialsError as e:
            raise EvChartFeatureStoreConnectionError(operation="Get", log_obj= log) from e

        except ClientError as e:
            if e.response["Error"]["Code"] == "ParameterNotFound":
                log.log_debug("Parameter does not exist")
                return None

            log.log_debug(f"parameter exists: {name}")
            log.log_level3_error(e)

        return parameter["Parameter"].get("Value")


    def get_feature_toggle_by_enum(self, feature: Feature, log: LogEvent):
        """
        parameter: Feature enum
        returns: feature toggle value, should be True or False
        """
        if not isinstance(feature, Feature):
            raise TypeError(f"{feature} is not of type Feature")
        return self.get_feature_toggle_by_name(feature.value, log)


    def get_active_feature_toggles(self, log_event: LogEvent) -> frozenset:
        """
        returns a set of all BE Feature Toggle members (as Feature enum)
        that are set to True, meaning that the feature toggle is active

        note: FE feature toggles without an associated BE feature toggle
        will NOT be present in this list
        """
        feature_toggles_set_to_true = []
        all_feature_toggles_list = self.get_all_feature_toggles(log_event)
        for ft in all_feature_toggles_list:
            if ft["Value"]:
                try:
                    feature_toggles_set_to_true.append(Feature(ft["Name"]))
                except ValueError:
                    # don't include feature in set if not defined in the backend feature enums
                    pass
        if feature_toggles_set_to_true:
            feature_toggle_set = frozenset(feature_toggles_set_to_true)
            return feature_toggle_set
        return {}
