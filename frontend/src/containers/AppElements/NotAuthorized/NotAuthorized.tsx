/**
 * General unauthorized page for the application.
 * @packageDocumentation
 **/
import { useNavigate } from "react-router";

import { Alert, Button, Grid, GridContainer } from "evchartstorybook";

import dots_gradient from "../../../assets/dots_gradient.svg";
import EVChARTFooter from "../../../components/Layout/Footer/EVChARTFooter";
import EVChARTHeader from "../../../components/Layout/Header/EVChARTHeader";

import "./NotAuthorized.css";

/**
 * NotAuthorizedPage
 * @returns the not authorized page for the application
 */
function NotAuthorizedPage() {
  /**
   * Method for changing the location / route
   */
  const navigate = useNavigate();

  return (
    <div id="main-content-container">
      <EVChARTHeader />
      <div id="main-content">
        <div className="not-authorized-page">
          <GridContainer>
            <Grid row id="notAuthorizedBanner">
              <Grid col={12}>
                <Alert type="error" headingLevel="h3" heading="You do not have access to this page">
                  Please contact your organization's administrator for access or contact us using one of the methods
                  available at the bottom of this page.
                </Alert>
              </Grid>
            </Grid>
            <Grid row id="notAuthorizedText">
              <Grid col={12}>
                <h1 className="align-center">You do not have access to this page</h1>
              </Grid>
            </Grid>
            <Grid row id="notAuthorizedDots">
              <Grid col={12}>
                <div className="align-center">
                  <img src={dots_gradient} />
                </div>
              </Grid>
            </Grid>
            <Grid row id="notAuthorizedReturnHome">
              <Grid col={12}>
                <div className="align-center">
                  <Button
                    type="button"
                    onClick={() => {
                      navigate("/");
                    }}
                  >
                    Return Home
                  </Button>
                </div>
              </Grid>
            </Grid>
          </GridContainer>
        </div>
      </div>
      <div className="splash-logo-footer">
        <EVChARTFooter showSplashLogo={true} />
      </div>
    </div>
  );
}

export default NotAuthorizedPage;
