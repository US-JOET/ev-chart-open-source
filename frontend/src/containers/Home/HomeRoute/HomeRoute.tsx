/**
 * Updated home page for the application, routes to relevant page.
 * @packageDocumentation
 **/
import { useEffect, useState } from "react";

import { Grid, GridContainer, Spinner } from "evchartstorybook";

import { isSRUser, isDRUser, isJOUser } from "../../../utils/authFunctions";
import { FeatureFlagEnum, getFeatureFlagValue, getFeatureFlagList } from "../../../utils/FeatureToggle";

import DRHome from "../DRHome/DRHome";
import Home from "../Home/Home";
import JOHome from "../JOHome/JOHome";

import "./HomeRoute.css";

/**
 * HomeRoute
 * @returns the appropriate landing page based on user type
 */
function HomeRoute() {
  /**
   * Feature flag management
   * Toggles:
   *  * JO PP Dashboard
   *  * JO SS Dashboard
   *  * DR PP Dashboard
   *  * DR SS Dashboard
   */
  const [isLoading, setIsLoading] = useState(false);
  const [joPPDashboardFeatureFlag, setJOPPDashboardFeatureFlag] = useState(false);
  const [joSSDashboardFeatureFlag, setJOSSDashboardFeatureFlag] = useState(false);
  const [drPPDashboardFeatureFlag, setDRPPDashboardFeatureFlag] = useState(false);
  const [drSSDashboardFeatureFlag, setDRSSDashboardFeatureFlag] = useState(false);
  useEffect(() => {
    setIsLoading(true);
    getFeatureFlagList()
      .then((results) => {
        setJOPPDashboardFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.JOPPDashboard));
        setJOSSDashboardFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.JOSSDashboard));
        setDRPPDashboardFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.DRPPDashboard));
        setDRSSDashboardFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.DRSSDashboard));
      })
      .finally(() => setIsLoading(false));
  }, []);

  /**
   * Determine what to render as the home screen based on the feature flags
   */
  let homePage;
  if (isSRUser()) {
    homePage = <Home />;
  } else if (isDRUser()) {
    if (drPPDashboardFeatureFlag || drSSDashboardFeatureFlag) {
      homePage = <DRHome />;
    } else {
      homePage = <Home />;
    }
  } else if (isJOUser()) {
    if (joPPDashboardFeatureFlag || joSSDashboardFeatureFlag) {
      homePage = <JOHome />;
    } else {
      homePage = <Home />;
    }
  }

  return isLoading ? (
    <GridContainer className="home-route">
      <Grid row>
        <Grid col className="spinner-content home-route__spinner">
          <Spinner></Spinner>
        </Grid>
      </Grid>
    </GridContainer>
  ) : (
    <>{homePage}</>
  );
}

export default HomeRoute;
