/**
 * Landing page for the joint office.
 * @packageDocumentation
 **/
import { useEffect, useState } from "react";

import { Grid, GridContainer } from "evchartstorybook";

import { Tab, Tabs, TabsList, TabPanel } from "@mui/base";

import { FeatureFlagEnum, getFeatureFlagValue, getFeatureFlagList } from "../../../utils/FeatureToggle";

import ProgramPerformanceDashboard from "../../../components/ProgramPerformance/ProgramPerformanceDashboard";

import "./JOHome.css";

/**
 * JOHome
 * @returns the landing page for the joint office
 */
function JOHome() {
  /**
   * Feature flag management
   * Toggles:
   *  * JO PP Dashboard
   *  * JO SS Dashboard
   */
  const [joPPDashboardFeatureFlag, setJOPPDashboardFeatureFlag] = useState(false);
  const [joSSDashboardFeatureFlag, setJOSSDashboardFeatureFlag] = useState(false);
  useEffect(() => {
    getFeatureFlagList().then((results) => {
      setJOPPDashboardFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.JOPPDashboard));
      setJOSSDashboardFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.JOSSDashboard));
    });
  }, []);

  return (
    <div id="jo-home-page">
      <GridContainer className="jo-home-container">
        <Grid row className="jo-welcome-container">
          <Grid col={8}>
            <h1 className="jo-welcome-header">Welcome to EV-ChART!</h1>
          </Grid>
        </Grid>
        {joSSDashboardFeatureFlag && joPPDashboardFeatureFlag ? (
          <Grid row gap className="jo-dashboard-tabs">
            <Grid col={12}>
              <Tabs defaultValue={"jo-ss-dashboard"}>
                <TabsList id="moduleDataTabsList">
                  <Tab id="jo-ss-dashboard" value="jo-ss-dashboard">
                    Submission Status Overview
                  </Tab>

                  <Tab id="jo-pp-dashboard" value="jo-pp-dashboard">
                    Program Performance
                  </Tab>
                </TabsList>

                <TabPanel value="jo-ss-dashboard" id="joSSDashboard">
                  <div>COMING SOON: JO SS Dashboard</div>
                </TabPanel>

                <TabPanel value="jo-pp-dashboard" id="joPPDashboard">
                  <ProgramPerformanceDashboard />
                </TabPanel>
              </Tabs>
            </Grid>
          </Grid>
        ) : (
          <div className="jo-pp-container">
            <ProgramPerformanceDashboard />
          </div>
        )}
      </GridContainer>
    </div>
  );
}

export default JOHome;
