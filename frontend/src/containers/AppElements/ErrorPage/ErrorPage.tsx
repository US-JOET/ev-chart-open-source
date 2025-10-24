/**
 * General error page for the application.
 * @packageDocumentation
 **/
import { useEffect, useState } from "react";
import { useNavigate } from "react-router";

import { CognitoJwtVerifier } from "aws-jwt-verify";

import { Button, Grid, GridContainer } from "evchartstorybook";

import { isFederal } from "../../../utils/authFunctions";
import { PATH_STATUS } from "../../../utils/pathConstants";
import { ROUTE_HOME, ROUTE_LOGIN, ROUTE_MAINTENANCE } from "../../../utils/routeConstants";

import dots_gradient from "../../../assets/dots_gradient.svg";
import EVChARTHeader from "../../../components/Layout/Header/EVChARTHeader";
import EVChARTFooter from "../../../components/Layout/Footer/EVChARTFooter";

import "./ErrorPage.css";

/**
 * ErrorPage
 * @returns the error page of the application
 */
function ErrorPage() {
  /**
   * Method for changing the location / route
   */
  const navigate = useNavigate();

  /**
   * Get the base url and environment variables
   */
  const BASE_URL = import.meta.env.VITE_PUBLIC_URL;
  const userPoolId = String(import.meta.env.VITE_USERPOOLID);
  const clientId = String(import.meta.env.VITE_CLIENTID);
  const localEnv = BASE_URL === "";

  /**
   * Get access token for endpoint authorization
   */
  const access_token = localStorage.getItem("access_token");

  /**
   * State variable for granting / rendering application to user
   */
  const [validUser, setValidUser] = useState(false);

  /**
   * Validate token and route to login if invalid
   */
  useEffect(() => {
    if (!access_token && !localEnv) {
      navigate(ROUTE_LOGIN);
    }

    const validateToken = async () => {
      const verifier = CognitoJwtVerifier.create({
        userPoolId: userPoolId,
        tokenUse: "access",
        clientId: clientId,
      });

      try {
        if (access_token) {
          await verifier.verify(access_token);
          console.log("Token is valid");
          setValidUser(true);
        }
      } catch {
        console.log("Token not valid!");
        navigate(ROUTE_LOGIN);
      }
    };
    if (access_token) {
      validateToken();
    }
  }, [access_token]);

  /**
   * Check if application is in maintenance mode
   * Users should all be routed to maintenance page if yes
   */
  async function checkMaintenanceMode() {
    /**
     * Get the api url from the environment variables
     */
    const API_URL = import.meta.env.VITE_API_URL;
    const BASE_URL = import.meta.env.VITE_PUBLIC_URL;
    try {
      const response = await fetch(`${API_URL}${PATH_STATUS}`, {
        method: "GET",
      });
      if (response.ok) {
        const data = await response.json();
        const maintenanceMode = data.maintenance;
        if (maintenanceMode && !isFederal()) {
          window.location.href = `${BASE_URL}${ROUTE_MAINTENANCE}`;
        }
      }
    } catch (error) {
      console.error("An error occurred:", error);
    }
  }
  useEffect(() => {
    checkMaintenanceMode();
  }, []);

  return (
    <>
      {validUser && (
        <>
          <EVChARTHeader />
          <div id="main-content">
            <div className="not-found-page">
              <GridContainer>
                <Grid row id="notFoundText">
                  <Grid col={12}>
                    <h1 className="align-center">This page does not exist</h1>
                  </Grid>
                </Grid>
                <Grid row id="notFoundDots">
                  <Grid col={12}>
                    <div className="align-center">
                      <img src={dots_gradient} />
                    </div>
                  </Grid>
                </Grid>
                <Grid row id="notFoundReturnHome">
                  <Grid col={12}>
                    <div className="align-center">
                      <Button
                        type="button"
                        onClick={() => {
                          navigate(ROUTE_HOME);
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
        </>
      )}
    </>
  );
}

export default ErrorPage;
