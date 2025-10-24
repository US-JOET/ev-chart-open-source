/**
 * Tooltip with the submission status details of the modules contained within the harvey ball icon.
 * Imported into the Submission Tracker table component.
 * @packageDocumentation
 **/
import { ReactElement } from "react";

import { Icon } from "evchartstorybook";

import { formatModuleNameLabel } from "../../../utils/ModuleName";

const moduleIdMap: Record<string, number> = {
  module2_priority: 2,
  module3_priority: 3,
  module4_priority: 4,
  module5_priority: 5,
  module6_priority: 6,
  module7_priority: 7,
  module8_priority: 8,
  module9_priority: 9,
};

const SubmissionDeadlineMap: Record<string, string> = {
  one_time: "March 1st",
  annual: "March 1st",
  quarter1: "April 30th",
  quarter2: "July 31st",
  quarter3: "October 31st",
  quarter4: "January 31st",
};

const ReportingPeriodLabelMap: Record<string, string> = {
  one_time: "One Time",
  annual: "Annual",
  quarter1: "Quarter 1",
  quarter2: "Quarter 2",
  quarter3: "Quarter 3",
  quarter4: "Quarter 4",
};

/**
 * Function to render the harvey ball icon based on the module hover status
 * @param hoverStatus the status of the modules contained for a given station and reporting period
 * (attention, submitted, some_submitted, not_required, not_applicable, not_submitted).
 * @returns the harvey ball icon
 */
export const SubmissionTrackerIcon = ({ hoverStatus }: { hoverStatus: string }): ReactElement => {
  let submissionTrackerIcon: ReactElement;
  switch (hoverStatus) {
    case "attention":
      submissionTrackerIcon = <Icon.TrackerBallAttention size={3} />;
      break;
    case "submitted":
      submissionTrackerIcon = <Icon.TrackerBallSubmitted size={3} className="icon-overflow-visible" />;
      break;
    case "some_submitted":
      submissionTrackerIcon = <Icon.TrackerBallPartialData size={3} className="icon-overflow-visible" />;
      break;
    case "not_required":
      submissionTrackerIcon = <Icon.TrackerBallNoDataRequired size={3} />;
      break;
    case "not_applicable":
      submissionTrackerIcon = <Icon.TrackerBallNoDataRequiredEver size={3} />;
      break;
    case "none_submitted":
    default:
      submissionTrackerIcon = <Icon.TrackerBallNoData size={3} className="icon-overflow-visible" />;
      break;
  }
  return submissionTrackerIcon;
};

/**
 * Function to render the label associated with the harvey ball icon based on the module hover status
 * @param hoverStatus the status of the modules contained for a given station and reporting period
 * (attention, submitted, some_submitted, not_required, not_applicable, not_submitted).
 * @returns the harvery ball icon's label
 */
const SubmissionTrackerIconLabel = ({ hoverStatus }: { hoverStatus: string }): ReactElement => {
  let submissionTrackerIconLabel: string;
  switch (hoverStatus) {
    case "attention":
      submissionTrackerIconLabel = "Module(s) require attention/review";
      break;
    case "submitted":
      submissionTrackerIconLabel = "Approved/Submitted Data for all Modules";
      break;
    case "some_submitted":
      submissionTrackerIconLabel = "Some Modules Approved/Submitted";
      break;
    case "not_required":
      submissionTrackerIconLabel = "No Modules Due Yet";
      break;
    case "not_applicable":
      submissionTrackerIconLabel = "Station Not Operational, No Submissions Required";
      break;
    case "none_submitted":
    default:
      submissionTrackerIconLabel = "No Modules Approved/Submitted";
      break;
  }
  return <>{submissionTrackerIconLabel}</>;
};

/**
 * Function to render the label for a given module's status
 * @param moduleStatus the status of the individual module displayed in the tooltip
 * (pending, submitted, not_submitted).
 * @returns the module status' label
 */
const ModuleStatusLabel = ({ moduleStatus }: { moduleStatus: string }): ReactElement => {
  let moduleStatusLabel: string;
  switch (moduleStatus) {
    case "pending":
      moduleStatusLabel = "At least 1 submission is either pending approval or is overdue";
      break;
    case "submitted":
      moduleStatusLabel = "At least 1 submission approved/submitted";
      break;
    case "not_submitted":
    default:
      moduleStatusLabel = "No submissions approved/submitted";
      break;
  }
  return <>{moduleStatusLabel}</>;
};

interface SubmissionTrackerTooltipContentsProps {
  data: Record<string, string>;
  reportingPeriod: string;
  reportingPeriodLabel: string;
}

/**
 * Component containing information about the modules' statuses
 * for the Submission Tracker Tooltip
 */
const SubmissionTrackerTooltipContents = ({
  data,
  reportingPeriod,
  reportingPeriodLabel,
}: SubmissionTrackerTooltipContentsProps) => {
  /**
   * Returns the list of keys from the API response with module data. Ex: 'module2_priority'
   */
  const modulePriorityKeys = Object.keys(data).filter((key) => key.startsWith("module"));

  switch (data.hover_status) {
    case "attention":
    case "submitted":
    case "some_submitted":
      return (
        <>
          {modulePriorityKeys.map((modulePriorityKey) => (
            <div key={modulePriorityKey} className="submission-tracker-tooltip__contents">
              <div className="submission-tracker-tooltip__module-name-label">
                {formatModuleNameLabel(moduleIdMap[modulePriorityKey])}
              </div>
              <div className="submission-tracker-tooltip__subheading">
                <ModuleStatusLabel moduleStatus={data[modulePriorityKey]} />
              </div>
            </div>
          ))}
        </>
      );
    case "none_submitted":
    default:
      return (
        <>
          <div className="submission-tracker-tooltip__contents">
            No modules have been approved/submitted for this reporting period. To upload module data, go to Data
            Submittals {">"} Module Data {">"} Select “Upload Module Data”
          </div>
          <div className="submission-tracker-tooltip__contents">
            {reportingPeriodLabel} submissions will be due on {SubmissionDeadlineMap[reportingPeriod]}
          </div>
        </>
      );
    case "not_required":
      return (
        <>
          <div className="submission-tracker-tooltip__contents">
            This is a upcoming reporting period and there are no modules required to be submitted/approved at this time.
          </div>
          <div className="submission-tracker-tooltip__contents">
            {reportingPeriodLabel} submissions will be due on {SubmissionDeadlineMap[reportingPeriod]}
          </div>
        </>
      );
    case "not_applicable":
      return (
        <>
          <div className="submission-tracker-tooltip__contents">
            No submission required - station was not operational during this reporting period.
          </div>
          <div className="submission-tracker-tooltip__contents">
            To update the station operational date go to Management {">"} Stations {">"} Identify station to edit {">"}{" "}
            Select Actions {">"} Edit
          </div>
        </>
      );
  }
};

interface SubmissionTrackerTooltipProps {
  data: Record<string, string>;
  reportingPeriod: string;
  reportingYear: string;
}

export const SubmissionTrackerTooltip = ({ data, reportingPeriod, reportingYear }: SubmissionTrackerTooltipProps) => {
  return (
    <div className="submission-tracker-tooltip">
      <div className="submission-tracker-tooltip__heading">
        <div>
          <SubmissionTrackerIconLabel hoverStatus={data.hover_status} />
        </div>
        <div>
          <SubmissionTrackerIcon hoverStatus={data.hover_status} />
        </div>
      </div>
      <div className="submission-tracker-tooltip__subheading">{`${ReportingPeriodLabelMap[reportingPeriod]}, ${reportingYear}`}</div>
      <div>
        <SubmissionTrackerTooltipContents
          data={data}
          reportingPeriod={reportingPeriod}
          reportingPeriodLabel={ReportingPeriodLabelMap[reportingPeriod]}
        />
      </div>
    </div>
  );
};
