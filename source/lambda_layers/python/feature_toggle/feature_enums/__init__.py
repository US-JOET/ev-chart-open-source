from enum import Enum


class Feature(Enum):
    ADD_USER = "add-user"
    NEW_USER_EMAIL = "new-user-email"
    SEND_EMAIL = "send-email"
    SUBMISSION_TRACKER = "submission-tracker"
    DATA_APPROVAL_REJECTION_EMAIL = "data-approval-rejection-email"
    STATION_AUTHORIZES_SR_EMAIL = "station-authorizes-sr-email"
    UNIQUE_CONSTRAINT_MODULE_2 = "unique-constraint-module-2"
    UNIQUE_CONSTRAINT_MODULE_3 = "unique-constraint-module-3"
    UNIQUE_CONSTRAINT_MODULE_4 = "unique-constraint-module-4"
    UNIQUE_CONSTRAINT_MODULE_5 = "unique-constraint-module-5"
    UNIQUE_CONSTRAINT_MODULE_6 = "unique-constraint-module-6"
    UNIQUE_CONSTRAINT_MODULE_7 = "unique-constraint-module-7"
    UNIQUE_CONSTRAINT_MODULE_8 = "unique-constraint-module-8"
    UNIQUE_CONSTRAINT_MODULE_9 = "unique-constraint-module-9"
    PRESIGNED_URL = "presigned-url"
    JO_PP_DASHBOARD_NETWORK_SIZE = "jo-pp-dashboard-network-size"
    JO_PP_DASHBOARD_RELIABILITY = "jo-pp-dashboard-reliability"
    JO_PP_DASHBOARD = "jo-pp-dashboard"
    DR_ST_DASHBOARD = "dr-st-dashboard"
    FILE_UPLOAD_FAIL_EMAIL = "file-upload-fail-email"
    INSERT_RDS_FAIL_EMAIL = "insert-rds-fail-email"
    DATA_PROCESSING_FAIL_EMAIL = "data-processing-fail-email"
    DATA_PROCESSING_SUCCESS_EMAIL = "data-processing-success-email"
    DATA_AWAITING_REVIEW_EMAIL = "data-awaiting-review-email"
    REMOVE_MODULE_DATA = "remove-module-data"
    S2S = "s2s"
    DB_MIGRATIONS_FEATURE_TOGGLE_EXAMPLE = \
        'db-migrations-feature-toggle-example'
    ADD_SR_ORG = "add-sr-org"
    JO_ADD_ORG = "jo-add-org"
    USE_RDS_PROXY = "use-rds-proxy"
    STATION_SUBMISSION_DETAILS = "station-submission-details"
    MODULE_5_NULLS = "module-five-nulls"
    REMOVE_STATION = "remove-station"
    BIZ_MAGIC = "biz-magic"
    ASYNC_BIZ_MAGIC_MODULE_2 = "async-biz-magic-module-2"
    ASYNC_BIZ_MAGIC_MODULE_3 = "async-biz-magic-module-3"
    ASYNC_BIZ_MAGIC_MODULE_4 = "async-biz-magic-module-4"
    ASYNC_BIZ_MAGIC_MODULE_5 = "async-biz-magic-module-5"
    ASYNC_BIZ_MAGIC_MODULE_9 = "async-biz-magic-module-9"
    SR_ADDS_STATION = "sr-adds-station"
    NETWORK_PROVIDER_TABLE = "network-provider-table"
    SUBMISSION_TRACKER_SUBRECIPIENT_FILTER = \
        "submission-tracker-subrecipient-filter"
    DATABASE_CENTRAL_CONFIG = "database-central-config"
    N_TIER_ORGANIZATIONS = "n-tier-organizations"
    CHECK_DUPLICATES_UPLOAD = "check-duplicates-upload"
    DR_PP_DASHBOARD_OFFICIAL_UPTIME ="dr-pp-dashboard-official-uptime"
    EXCLUDED_OUTAGES_MODULE_FOUR = "excluded-outages-module-four"
    REGISTER_NON_FED_FUNDED_STATION = "register-non-fed-funded-station"
    QUERY_DOWNLOAD_REFACTOR = "query-download-refactor"


# Use the same name as the real feature toggle and the value being the environments where the
# pseudo-feature will be used and set as "True".
class PseudoFeature(Enum):
    # Only Dev uses the real feature toggle due to development processes that require the ability to
    # turn it off.
    PRESIGNED_URL = ["test", "qa", "preprod", "prod"]
