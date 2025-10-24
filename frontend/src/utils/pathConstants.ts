/**
 * Constants for api endpoints pathnames
 *
 * Note: Written as constants so that pathnames can be computed from one another.
 */
export const PATH_AUTHORIZATIONS = "/authorizations";
export const PATH_DASHBOARD = "/dashboard";
export const PATH_FEATURES = "/features";
export const PATH_MODULE = "/module";
export const PATH_ORG = "/org";
export const PATH_STATIONS = "/stations";
export const PATH_STATUS = "/status";
export const PATH_TOKEN = "/token";
export const PATH_UI = "/ui";
export const PATH_USERS = "/users";

export const PATH_DASHBOARD_SUBMISSION_DETAILS = `${PATH_DASHBOARD}/submission-details`;
export const PATH_DASHBOARD_PROGRAM_PERFORMANCE = `${PATH_DASHBOARD}/program-performance`;
export const PATH_DASHBOARD_PP_CAPITAL_COSTS = `${PATH_DASHBOARD_PROGRAM_PERFORMANCE}/capital-costs`;
export const PATH_DASHBOARD_PP_ENERGY_USAGE = `${PATH_DASHBOARD_PROGRAM_PERFORMANCE}/energy-usage`;
export const PATH_DASHBOARD_PP_NETWORK_SIZE = `${PATH_DASHBOARD_PROGRAM_PERFORMANCE}/federally-funded-network-size`;
export const PATH_DASHBOARD_PP_MAINTENANCE = `${PATH_DASHBOARD_PROGRAM_PERFORMANCE}/maintenance-costs`;
export const PATH_DASHBOARD_PP_RELIABILITY = `${PATH_DASHBOARD_PROGRAM_PERFORMANCE}/reliability`;


export const PATH_SUB_RECIPIENTS = `${PATH_ORG}/subrecipients`;
export const PATH_DIRECT_RECIPIENTS = `${PATH_ORG}/direct-recipients`;

export const PATH_MODULE_DATA = `${PATH_MODULE}/data`;
export const PATH_MODULE_DECISION = `${PATH_MODULE}/decision`;
export const PATH_MODULE_DETAILS = `${PATH_MODULE}/details`;
export const PATH_MODULE_DOWNLOAD = `${PATH_MODULE}/download`;
export const PATH_DRAFT_SUBMITTED = `${PATH_MODULE}/draft-submitted`;
export const PATH_MODULE_HISTORY_LOG = `${PATH_MODULE}/history-log`;
export const PATH_MODULE_IMPORT = `${PATH_MODULE}/import`;
export const PATH_MODULE_IMPORT_ERROR_DATA = `${PATH_MODULE}/import-error-data`;
export const PATH_MODULE_REMOVE = `${PATH_MODULE}/remove`;
export const PATH_MODULE_SUBMIT = `${PATH_MODULE}/submit`;
export const PATH_MODULE_SUBMISSION_APPROVAL = `${PATH_MODULE}/submission-approval`;
export const PATH_MODULE_SUBMISSION_TRACKER = `${PATH_MODULE}/submission-tracker`;
export const PATH_SUBMITTING_NULL = `${PATH_MODULE}/submitting-null`;

export const PATH_STATION_ID = `${PATH_STATIONS}/station-id`;
export const PATH_STATION_REMOVE = `${PATH_STATION_ID}/remove`;
export const PATH_STATION_ORG_ID = `${PATH_STATIONS}/org-id`;

export const PATH_COLUMN_DEFINITIONS = `${PATH_UI}/column-definitions`;
export const PATH_NETWORK_PROVIDERS = `${PATH_UI}/network-providers`;
export const PATH_REPORTING_YEARS = `${PATH_UI}/reporting-years`;
export const PATH_UPLOAD_OPTIONS = `${PATH_UI}/upload-options`;
