/**
 * Constants for route pathnames
 *
 * Note: Written as constants so that pathnames can be computed from one another.
 */
export const ROUTE_HOME = "/";
export const ROUTE_EDIT = "/edit";
export const ROUTE_HISTORY = "/history";
export const ROUTE_LOGIN = "/login";
export const ROUTE_MAINTENANCE = "/maintenance";
export const ROUTE_MANAGEMENT = "/management";
export const ROUTE_MODULE = "/module";
export const ROUTE_MODULE_DATA = "/module-data";
export const ROUTE_NOT_AUTHORIZED = "/not-authorized";
export const ROUTE_NOT_FOUND = "/not-found";
export const ROUTE_QUERY_DOWNLOAD = "/query-download";
export const ROUTE_SUBMISSION_TRACKER = "/";
export const ROUTE_RESOURCES = "/resources";

/**
 * Management Routes
 */
//Add Organizations
export const SUB_ROUTE_ADD_ORGANIZATION = "/add-organization";
export const ROUTE_ADD_SR_ORG = `${ROUTE_MANAGEMENT}${SUB_ROUTE_ADD_ORGANIZATION}`;

//Users
export const SUB_ROUTE_ADD_USER = "/add-user";
export const ROUTE_ADD_USER = `${ROUTE_MANAGEMENT}${SUB_ROUTE_ADD_USER}`;
export const SUB_ROUTE_USERS = "/users";
export const ROUTE_USERS = `${ROUTE_MANAGEMENT}${SUB_ROUTE_USERS}`;

//Authorize Contractors
export const ROUTE_AUTHROIZE_CONTRACTORS = "/authorize-contractors";

//Stations
export const SUB_ROUTE_STATIONS = "/stations";
export const ROUTE_STATIONS = `${ROUTE_MANAGEMENT}${SUB_ROUTE_STATIONS}`;
export const SUB_ROUTE_STATION_REGISTRATION = "/station-registration";
export const ROUTE_STATION_REGISTRATION = `${ROUTE_MANAGEMENT}${SUB_ROUTE_STATION_REGISTRATION}`;
export const SUB_ROUTE_STATION_ID = "/station-id";
export const ROUTE_STATION_ID = `${ROUTE_STATIONS}${SUB_ROUTE_STATION_ID}`;

/**
 * Resources Routes
 */
export const SUB_ROUTE_DIRECT_RECIPIENTS = "/direct-recipients";
export const SUB_ROUTE_GETTING_STARTED = "/getting-started";
export const SUB_ROUTE_NETWORK_PROVIDERS = "/network-providers";
export const SUB_ROUTE_PROGRAM_METRICS = "/how-are-the-program-performance-metrics-calculated";
export const ROUTE_DIRECT_RECIPIENTS = `${ROUTE_RESOURCES}${SUB_ROUTE_DIRECT_RECIPIENTS}`;
export const ROUTE_NETWORK_PROVIDERS = `${ROUTE_RESOURCES}${SUB_ROUTE_NETWORK_PROVIDERS}`;
export const ROUTE_GETTING_STARTED = `${ROUTE_RESOURCES}${SUB_ROUTE_GETTING_STARTED}`;
export const ROUTE_TECHNICAL_NOTES_PROGRAM_PERFORMANCE = `${ROUTE_RESOURCES}${SUB_ROUTE_PROGRAM_METRICS}`;

// Submission tracker sub paths
export const ROUTE_STATION_SUBMISSION_DETAILS = `${ROUTE_SUBMISSION_TRACKER}station-submission-details`;

/**
 * Enum for tab values
 *
 * Used with react-router-dom's navigate() function to navigate to a specific tab on a page.
 */
export enum TabEnum {
  DRProgramPerformance = "dr-pp-dashboard",
  DRSubmissionTracker = "dr-submission-tracker",
}
