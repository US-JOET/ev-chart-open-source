from feature_toggle.feature_enums import Feature
import pandas


def allow_null_federal_maintenance(feature_toggle_set, df):
    transform_df = df.copy()
    if Feature.MODULE_5_NULLS in feature_toggle_set:
        correct_nulls = (
            transform_df['maintenance_cost_total']
            .astype(str)
            .str.lower()
        ) == "null"
        transform_df.loc[correct_nulls, ['maintenance_cost_total']] = None

    transform_df['maintenance_cost_total'] = (
        pandas.to_numeric(transform_df['maintenance_cost_total'])
        .convert_dtypes()
    )
    return transform_df
