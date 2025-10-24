/**
 * Login page for the application.
 * @packageDocumentation
 **/
import { useEffect, useState } from "react";
import { useNavigate } from "react-router";

import { jwtDecode } from "jwt-decode";

import { Alert, Button, Grid, GridContainer, Header, Title } from "evchartstorybook";

import { CustomJwtPayload } from "../../interfaces/customJwtPayload";

import { PATH_TOKEN } from "../../utils/pathConstants";
import { ROUTE_HOME } from "../../utils/routeConstants";

import dots_gradient from "../../assets/dots_gradient.svg";
import logo from "../../assets/horizontal_logo-baa57ff6.png";
import EVChARTFooter from "../../components/Layout/Footer/EVChARTFooter";

import "./Login.css";

/**
 * Login page
 * @returns the login page for the application
 */
function Login() {
  /**
   * Method for changing the location / route
   */
  const navigate = useNavigate();

  /**
   * Get the api/base url and environment variables
   */
  const API_URL = import.meta.env.VITE_API_URL;
  const BASE_URL = import.meta.env.VITE_PUBLIC_URL;
  const clientId = import.meta.env.VITE_CLIENTID;
  const hostname = import.meta.env.VITE_HOSTNAME;
  const region = import.meta.env.VITE_REGION;
  const localEnv = BASE_URL === "";

  /**
   * State variable for rendering "No Access" alert
   */
  const [noAccessAlert, setNoAccessAlert] = useState(false);

  /**
   * State variable for rendering idle account alert
   */
  const [idleAccountAlert, setIdleAcountAlert] = useState(false);

  /**
   * State variable for rendering sign out due to inactivity alert
   */
  const [inactivtiySignOut, setInactivitySignOut] = useState(false);

  /**
   * State variable for rendering voluntary user sign out alert
   */
  const [userSignedOut, setUserSignedOut] = useState(false);

  /**
   * State variable for rendering expired user alert
   */
  const [expiredUserAlert, setExpiredUserAlert] = useState(false);

  /**
   * Get the URL from the browser to parse out search params
   */
  const url = new URL(window.location.href);

  /**
   * Get the code from the browser URL to exchange for jwt
   */
  const code = url.searchParams.get("code");

  /**
   * Used for testing, login via a username and password combo in the search params
   */
  const username = url.searchParams.get("username");
  const password = url.searchParams.get("password");

  /**
   * Determine sign in method and fetch jwt
   */
  useEffect(() => {
    const fetchJWT = async (params: string) => {
      let jwtEndpoint = "";
      if (params === "code") {
        jwtEndpoint = `${API_URL}${PATH_TOKEN}?code=${code}`;
      } else if (params === "usernameAndPassword") {
        jwtEndpoint = `${API_URL}${PATH_TOKEN}?username=${username}&password=${password}`;
      } else if (params === "localEnv") {
        const envUsername = import.meta.env.VITE_USERNAME;
        const envPassword = import.meta.env.VITE_PASSWORD;
        jwtEndpoint = `${API_URL}${PATH_TOKEN}?username=${envUsername}&password=${envPassword}`;
      }
      try {
        const response = await fetch(jwtEndpoint, {
          method: "GET",
        });
        if (response.ok) {
          const JwtToken = await response.json();
          const access_token = JwtToken.access_token;
          const id_token = JwtToken.id_token;
          try {
            if (id_token) {
              const decoded = jwtDecode(id_token) as CustomJwtPayload;
              const status = decoded.account_status;
              if (status === "Deactivated") {
                url.searchParams.delete("code");
                window.history.replaceState(null, "", url.href);
                setIdleAcountAlert(true);
                return;
              } else if (status === "Expired") {
                url.searchParams.delete("code");
                window.history.replaceState(null, "", url.href);
                setExpiredUserAlert(true);
                return;
              }
              const scope = decoded.scope;
              if (!scope) {
                console.log("No scope found. User does not have access to EV-ChART.");
                url.searchParams.delete("code");
                window.history.replaceState(null, "", url.href);
                setNoAccessAlert(true);
                return;
              }
            }
            if (access_token) {
              console.log("Token is valid.");
            }
          } catch {
            localStorage.clear();
            console.log("Token not valid!");
          }
          localStorage.setItem("access_token", JwtToken.access_token);
          localStorage.setItem("id_token", JwtToken.id_token);
          localStorage.setItem("refresh_token", JwtToken.refresh_token);
          navigate(ROUTE_HOME);
        }
      } catch (error) {
        console.error("An error occurred:", error);
      }
    };
    if (code) {
      fetchJWT("code");
    }
    if (localEnv) {
      fetchJWT("localEnv");
    }
    if (username && password) {
      fetchJWT("usernameAndPassword");
    }
  });

  /**
   * Check if signout or inactive alerts need to be set
   */
  useEffect(() => {
    if (localStorage.getItem("inactiveSignout") === "true") {
      setInactivitySignOut(true);
      localStorage.clear();
    }
    if (localStorage.getItem("userSignout") === "true") {
      setUserSignedOut(true);
      localStorage.clear();
    }
  }, []);

  return (
    <>
      <div id="main-content">
        <div id="login-page">
          {(!code || noAccessAlert || idleAccountAlert || userSignedOut || expiredUserAlert) && (
            <>
              <GridContainer>
                <Header extended={true}>
                  <div className="usa-navbar">
                    <Title
                      id="basic-logo"
                      logo={logo}
                      subtitle="Electric Vehicle Charging Analytics and Reporting Tool"
                    >
                      EV-ChART
                    </Title>
                  </div>
                </Header>
                <Grid row gap>
                  <Grid col={12}>
                    {noAccessAlert && (
                      <Alert
                        className="no-access-alert"
                        type="error"
                        headingLevel="h1"
                        heading="You do not have access to EV-ChART"
                      >
                        Please contact your organization's administrator for access or contact EV-ChART using one of the
                        methods available at the bottom of this page.
                      </Alert>
                    )}
                    {idleAccountAlert && (
                      <Alert
                        className="no-access-alert"
                        type="error"
                        headingLevel="h1"
                        heading="You no longer have access to EV-ChART"
                      >
                        Your account has been idle for over 400 days and is no longer active within the EV-ChART system.
                        Contact your program adminstrator to regain account access.
                      </Alert>
                    )}
                    {expiredUserAlert && (
                      <Alert
                        className="no-access-alert"
                        type="error"
                        headingLevel="h1"
                        heading="You no longer have access to EV-ChART"
                      >
                        Your invitation to access EV-ChART has expired since you did not log into EV-ChART for at least
                        30 days after account creation. To regain access EV-ChART,{" "}
                        <a
                          href="https://driveelectric.gov/contact/?inquiry=evchart"
                          rel="noopener noreferrer"
                          target="_blank"
                          className="evchart-link-reference"
                        >
                          contact the Joint Office
                        </a>
                        .
                      </Alert>
                    )}
                    {inactivtiySignOut && (
                      <Alert
                        className="no-access-alert"
                        type="info"
                        headingLevel="h1"
                        heading="You have been signed out due to inactivity"
                      >
                        For your account security, you have been signed out of your session.
                      </Alert>
                    )}
                    {userSignedOut && (
                      <Alert className="no-access-alert" type="info" headingLevel="h1">
                        You have been signed out successfully
                      </Alert>
                    )}
                  </Grid>
                </Grid>
                <Grid row gap className="login-container">
                  <Grid col={4}>
                    <Grid className="sign-in-container">
                      <h1 className="sign-in-header">Sign in</h1>
                      <Button
                        type="button"
                        className="oneid-button"
                        onClick={() =>
                          (window.location.href = `https://${hostname}.auth-fips.${region}.amazoncognito.com/oauth2/authorize?client_id=${clientId}&response_type=code&scope=email+openid+profile&redirect_uri=${API_URL}/login`)
                        }
                      >
                        Sign in with OneID
                      </Button>
                      <p className="sign-in-text">
                        By clicking the above button, you agree to the{" "}
                        <a
                          href="https://driveelectric.gov/evchart-terms"
                          target="_blank"
                          className="sign-in-header"
                          rel="noreferrer"
                        >
                          EV-ChART Terms of Use
                        </a>
                        . Access to EV-ChART is managed through the U.S. Department of Energy (DOE) OneID Authentication
                        Hub (OneID). Upon clicking the above button, you will be redirected to OneID where you will
                        select a method to authenticate your identification. These methods include your DOE PIV card or
                        your organization's DOE site account. If your organization is not affiliated with DOE and/or is
                        not displayed as an organization option under "PIV Card", please create an account and confirm
                        your identify through login.gov. All EV-ChART users must have a method for identity
                        authentication established to access the application.
                      </p>
                    </Grid>
                  </Grid>
                  <Grid col={8}>
                    <Grid className="summary-information-container">
                      <h1>Submit, Review, & Analyze EV Charging Infrastructure Data</h1>
                      <img className="svg-dots" src={dots_gradient} />
                      <p>
                        EV-ChART is the centralized hub for collecting the data required in 23 CFR 680.112 which will:
                      </p>
                      <div className="information-summary-bullets">
                        <ul className="login-list">
                          <li className="login-list-item">Streamline and standardize the data submission.</li>
                          <li className="login-list-item">Integrate a set of reporting and analytic capabilities.</li>
                          <li className="login-list-item">Empower data sharing across stakeholders.</li>
                        </ul>
                      </div>
                      <div className="evchart-link-reference">
                        <a href="https://driveelectric.gov/evchart" target="_blank" rel="noreferrer">
                          Learn about the Joint Office & EV-ChART Requirements
                        </a>
                        <p>
                          <br />OMB #: 2125-0674 | Expires: 07/31/2028
                        </p>
                      </div>
                    </Grid>
                  </Grid>
                </Grid>
              </GridContainer>
            </>
          )}
        </div>
      </div>
      <div className="splash-logo-footer">
        <EVChARTFooter showSplashLogo={true} />
      </div>
    </>
  );
}

export default Login;
