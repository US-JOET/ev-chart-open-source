import { featureFlag } from "../interfaces/featureFlag-interface";
import { PATH_FEATURES } from "./pathConstants";

export enum FeatureFlagEnum {
  AddUser = "add-user",
  SubmissionTracker = "submission-tracker",
  JOPPDashboard = "jo-pp-dashboard",
  JOSSDashboard = "jo-ss-dashboard",
  DRPPDashboard = "dr-pp-dashboard",
  DRSSDashboard = "dr-ss-dashboard",
  PresignedUrl = "presigned-url",
  RemoveModule = "remove-module",
  InsertRDSFailEmail = "insert-rds-fail-email",
  DataProcessingFailEmail = "data-processing-fail-email",
  DataProcessingSuccessEmail = "data-processing-success-email",
  DataAwaitingReviewEmail = "data-awaiting-review-email",
  AddSROrg = "add-sr-org",
  JOAddOrg = "jo-add-org",
  StationSubmissionDetails = "station-submission-details",
  StationSubmissionDetailsReportingYear = "station-submission-details-reporting-year",
  ModuleFiveNulls = "module-five-nulls",
  RemoveStation = "remove-station",
  SRAddsStation = "sr-adds-station",
  DRPPDashboardReportingYear = "dr-pp-dashboard-reporting-year",
  BizMagic = "biz-magic",
  SubmissionTrackerSubrecipientFilter = "submission-tracker-subrecipient-filter",
  DRPPDashboardDynamicUnits = "dr-pp-dashboard-dynamic-units",
  DRPPDashboardOfficialUptime = "dr-pp-dashboard-official-uptime",
  ExcludedOutagesModuleFour = "excluded-outages-module-four",
  NTierOrganizations = "n-tier-organizations",
  ResourcesTechnicalNotesDRPPDashboard = "resources-technical-notes-dr-pp-dashboard",
  RegisterNonFedFundedStation = "register-non-fed-funded-station",
  QueryDownloadRefactor = "query-download-refactor"
}

export async function getFeatureFlagList(): Promise<featureFlag[]> {
  const API_URL = import.meta.env.VITE_API_URL;
  let featureFlagList = [] as featureFlag[];
  try {
    const response = await fetch(`${API_URL}${PATH_FEATURES}`, {
      method: "GET",
    });
    if (response.ok) {
      const data = await response.json();
      const featureList = data as featureFlag[];
      featureFlagList = featureList;
    }
  } catch (error) {
    console.error("An error occurred:", error);
  } finally {
    return featureFlagList;
  }
}

export function getFeatureFlagValue(featureFlagList: featureFlag[], featureName: FeatureFlagEnum): boolean {
  const feature = featureFlagList?.find((feature) => feature.Name === featureName.toString());
  return feature?.Value ?? false;
}
