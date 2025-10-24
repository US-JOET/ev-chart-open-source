"""
Row-level validation checks for Module 9 uploads performed during AsyncBizMagic.
Module-specific business logic is applied and verified
"""
from database_central_config import DatabaseCentralConfig
from feature_toggle.feature_enums import Feature
from error_report_messages_enum import ErrorReportMessages


def validate_empty_capital_install_costs(validation_options):
    """
    Convenience function that validates that only the fields regarding capitall install
    costs are empty. If other required fields are found empty, the function will flag
    this as an error. For each row of invalid data present within the dataframe, its
    details regarding the name and location of the invalid data, are stored in a list
    of dicts and is returned as a whole conditions object.
    """
    feature_toggle_set = validation_options.get("feature_toggle_set")
    df = validation_options.get("df")

    if Feature.ASYNC_BIZ_MAGIC_MODULE_9 not in feature_toggle_set:
        return {"conditions": []}

    if Feature.DATABASE_CENTRAL_CONFIG in feature_toggle_set:
        config = DatabaseCentralConfig()
        required_fields = config.required_fields(9)
        empty_capital_install_cost_fields = config.required_empty_allowed_fields(9).union(config.recommended_fields(9))
        empty_capital_install_cost_fields.remove("der_acq_owned")
    else:
        required_fields = [
            "real_property_cost_total",
            "real_property_cost_federal",
            "equipment_cost_total",
            "equipment_cost_federal",
            "equipment_install_cost_total",
            "equipment_install_cost_federal",
            "der_cost_total",
            "der_cost_federal",
            "der_install_cost_total",
            "der_install_cost_federal",
            "dist_sys_cost_total",
            "dist_sys_cost_federal",
            "service_cost_total",
            "service_cost_federal",
        ]
        empty_capital_install_cost_fields = [
            "real_property_cost_total",
            "equipment_cost_total",
            "equipment_install_cost_total",
            "equipment_install_cost_elec",
            "equipment_install_cost_const",
            "equipment_install_cost_labor",
            "equipment_install_cost_other",
            "der_cost_total",
            "der_install_cost_total",
            "dist_sys_cost_total",
            "service_cost_total",
        ]

    validated_df = df.copy()

    # Add recommended columns to data irrespective of central config being enabled.
    recommended_fields = [col for col in empty_capital_install_cost_fields if col not in required_fields]
    for field in recommended_fields:
        if field not in validated_df:
            validated_df[field] = None

    empty_capital_install_cost_df = validated_df[list(empty_capital_install_cost_fields)]
    validated_df["valid_empty_row"] = (empty_capital_install_cost_df == "").all(axis=1)

    required_fields_df = validated_df[list(required_fields)]
    validated_df["valid_all_required"] = (required_fields_df != "").all(axis=1)

    # constructs conditions object based on rows with missing required fields
    return {
        "conditions": [
            {
                "error_row": row,
                "error_description": (
                    ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name=column)
                ),
                "header_name": column,
            }
            for row in validated_df[
                ~validated_df[["valid_empty_row", "valid_all_required"]].any(axis=1)
            ].index
            for column in validated_df.loc[
                [row], (validated_df.loc[[row]] == "").any()
            ].columns.tolist()
            if column in required_fields
        ]
    }
