/**
 * Direct recipient home / landing page.
 * @packageDocumentation
 **/
import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";

import { Tab, Tabs, TabsList, TabPanel } from "@mui/base";
import moment from "moment";

import { Alert, Grid, GridContainer } from "evchartstorybook";

import { isAdmin, isDRUser } from "../../../utils/authFunctions";
import { FeatureFlagEnum, getFeatureFlagValue, getFeatureFlagList } from "../../../utils/FeatureToggle";
import { getOrgName } from "../../../utils/getJWTInfo";
import { TabEnum } from "../../../utils/routeConstants";

import SubmissionTracker from "../../SubmissionTracker/SubmissionTracker";
import ProgramPerformanceDashboard from "../../../components/ProgramPerformance/ProgramPerformanceDashboard";
import { getDueDateAlert } from "../DueDateAlert";

import "./DRHome.css";

/**
 * DRHome
 * @returns the direct recipient home / landing page
 */
function DRHome() {
  /**
   * Feature flag management
   * Toggles:
   *  * Program Performance Dashboard
   *  * Submission Status Dashboard
   *  * Submission Tracker
   */
  const [drPPDashboardFeatureFlag, setDRPPDashboardFeatureFlag] = useState(false);
  const [drSSDashboardFeatureFlag, setDRSSDashboardFeatureFlag] = useState(false);
  const [submissionTrackerFeatureFlag, setSubmissionTrackerFeatureFlag] = useState(false);
  useEffect(() => {
    getFeatureFlagList().then((results) => {
      setDRPPDashboardFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.DRPPDashboard));
      setDRSSDashboardFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.DRSSDashboard));
      setSubmissionTrackerFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.SubmissionTracker));
    });
  }, []);

  /**
   * Get organization name for header
   */
  const orgName = getOrgName();

  /**
   * State variables to render due date alert information
   */
  const [showDueDateAlert, setShowDueDateAlert] = useState<boolean>(false);
  const [dueDateHeading, setDueDateHeading] = useState<string>("");
  const [dueDateText, setDueDateText] = useState<string>("");

  /**
   * Check if there are any upcoming due dates to render due date alert
   */
  useEffect(() => {
    const today = moment();
    const { showAlert, heading, text } = getDueDateAlert(today);
    setShowDueDateAlert(showAlert);
    setDueDateHeading(heading);
    setDueDateText(text);
  }, []);

  /**
   * State passed through the application to the DR Home page
   */
  const { state } = useLocation();

  /**
   * State variable for the current tab selection
   */
  const [currentTab, setCurrentTab] = useState(state && state.startTab ? state.startTab : TabEnum.DRSubmissionTracker);

  /**
   * Function to change the tab value
   * @param e the tab to change to
   */
  const setTabValue = (e: any) => {
    setCurrentTab(e.target.id);
  };

  /**
   * Determine which tab to make the current tab based on feature flags
   */
  useEffect(() => {
    if (!state || !state.startTab) {
      setCurrentTab(submissionTrackerFeatureFlag ? TabEnum.DRSubmissionTracker : TabEnum.DRProgramPerformance);
    }
  }, [submissionTrackerFeatureFlag]);

  return (
    <div id="dr-home-page">
      <GridContainer className="dr-home-container">
        <Grid row className="dr-welcome-container">
          <Grid col={8}>
            <h1 className="dr-welcome-header">{orgName}</h1>
          </Grid>
        </Grid>
        <Grid row>
          <Grid col={12}>
            {isDRUser() && showDueDateAlert && (
              <Alert className="dr-due-date-banner" type="warning" headingLevel="h3" heading={dueDateHeading}>
                {dueDateText}
              </Alert>
            )}
          </Grid>
        </Grid>

        {(drSSDashboardFeatureFlag || drPPDashboardFeatureFlag) && (
          <Grid row gap className="dr-dashboard-tabs">
            <Grid col={12}>
              <Tabs value={currentTab}>
                <TabsList onClick={setTabValue} id="moduleDataTabsList">
                  {submissionTrackerFeatureFlag && (
                    <Tab id="dr-submission-tracker" value={TabEnum.DRSubmissionTracker}>
                      Submission Tracker
                    </Tab>
                  )}
                  {drSSDashboardFeatureFlag && (
                    <Tab id="dr-ss-dashboard" value="dr-ss-dashboard">
                      Submission Status Overview
                    </Tab>
                  )}
                  {drPPDashboardFeatureFlag && (
                    <Tab id="dr-pp-dashboard" value={TabEnum.DRProgramPerformance}>
                      Program Performance
                    </Tab>
                  )}
                </TabsList>
                {drSSDashboardFeatureFlag && (
                  <TabPanel value="dr-ss-dashboard" id="drSSDashboard">
                    <div>COMING SOON: DR SS Dashboard</div>
                  </TabPanel>
                )}
                {submissionTrackerFeatureFlag && (
                  <TabPanel id="drSubmissionTracker" value={TabEnum.DRSubmissionTracker}>
                    <SubmissionTracker />
                  </TabPanel>
                )}
                {drPPDashboardFeatureFlag && (
                  <TabPanel id="drPPDashboard" value={TabEnum.DRProgramPerformance}>
                    <ProgramPerformanceDashboard />
                  </TabPanel>
                )}
              </Tabs>
            </Grid>
          </Grid>
        )}
      </GridContainer>
    </div>
  );
}

export default DRHome;
