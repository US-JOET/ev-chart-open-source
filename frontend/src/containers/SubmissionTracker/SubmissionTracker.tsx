/**
 * Submission Tracker for module uploads.
 * @packageDocumentation
 **/
import { useState } from "react";

import { Alert, GridContainer, Grid, Icon, Tooltip } from "evchartstorybook";

import { getDashboardUpdatedTime } from "../../utils/dashboard";

import SubmissionTrackerLegend from "../../components/SubmissionTracker/SubmissionTrackerLegend/SubmissionTrackerLegend";
import SubmissionTrackerTable from "../../components/SubmissionTracker/SubmissionTrackerTable/SubmissionTrackerTable";
import CustomLink from "../../components/Tooltip/tooltips";

import "./SubmissionTracker.css";

function SubmissionTracker() {
  /**
   * State variable for controlling the updated time
   */
  const [dashboardUpdatedTime, setDashboardUpdatedTime] = useState<string>(getDashboardUpdatedTime());
  const updateDashboardTime = () => {
    const dashboardUpdatedTime = getDashboardUpdatedTime();
    setDashboardUpdatedTime(dashboardUpdatedTime);
  };

  return (
    <>
      <GridContainer className="submission-tracker-container">
        <Grid row>
          <Grid col={12}>
            <h2 className="program-performance-header">Submission Tracker</h2>
            <div className="pp-dashboard-time fixed-width-tooltip">
              <div className="program-performance-time">Dashboard Updated: {dashboardUpdatedTime}</div>
              <Tooltip
                label={
                  "Timestamp indicates the most recent refresh of the data displayed on the dashboard. Changing the parameters or reloading the page triggers a new timestamp."
                }
                className="submission-tracker__dashboard-updated-tooltip"
                asCustom={CustomLink}
              >
                <Icon.InfoOutline />
              </Tooltip>
            </div>
          </Grid>
        </Grid>
        <Grid row gap className="submission-tracker-overview-text">
          <Grid col={12}>
            <p>
              The submission tracker is a high-level overview of progress towards a station having at least one
              submission for each module in the reporting period. Note that non-federally funded stations are excluded
              from the submission tracker.
            </p>
          </Grid>
        </Grid>
        <Alert type="info" headingLevel="h4" className="submission-tracker-info-alert">
          <div className="heading">Review your data for quality and completeness</div>
          <div className="text">
            Since the submission tracker reflects self-reported data, review submissions closely to ensure data is
            complete (i.e., all data fields and ports are accounted for once approved/submitted).
          </div>
        </Alert>

        <Grid row gap>
          <Grid col={12}>
            <SubmissionTrackerLegend />
          </Grid>
        </Grid>
        <SubmissionTrackerTable updateTime={updateDashboardTime} />
      </GridContainer>
    </>
  );
}

export default SubmissionTracker;
