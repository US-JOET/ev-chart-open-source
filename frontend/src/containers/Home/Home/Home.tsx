/**
 * Original homepage for the application.
 * @packageDocumentation
 **/
import { useEffect, useState } from "react";
import { useNavigate } from "react-router";

import moment from "moment";

import { Alert, Button, Grid, GridContainer, SummaryBox, SummaryBoxContent, SummaryBoxHeading } from "evchartstorybook";

import { isDRUser, isSRUser } from "../../../utils/authFunctions";
import { FeatureFlagEnum, getFeatureFlagValue, getFeatureFlagList } from "../../../utils/FeatureToggle";
import { getScope } from "../../../utils/getJWTInfo";
import {
  ROUTE_MODULE_DATA,
  ROUTE_STATION_REGISTRATION,
  ROUTE_STATIONS,
  ROUTE_SUBMISSION_TRACKER,
  ROUTE_USERS,
  TabEnum,
} from "../../../utils/routeConstants";

import GettingStarted from "../../Resources/GettingStarted/GettingStarted";
import { getDueDateAlert } from "../DueDateAlert";

import "./Home.css";

interface ContentMapping {
  [key: string]: React.ReactNode;
}

function Home() {
  /**
   * Method for changing the location / route
   */
  const navigate = useNavigate();

  /**
   * Feature flag management
   * Toggles the submission tracker
   */
  const [submissionTrackerFeatureFlag, setSubmissionTrackerFeatureFlag] = useState(false);
  useEffect(() => {
    getFeatureFlagList().then((results) => {
      setSubmissionTrackerFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.SubmissionTracker));
    });
  }, []);

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
   * Get the scope of the current user to render relevant content
   */
  const userScope = getScope();

  const joetSummaryBox = (
    <>
      EV-ChART is the centralized hub for collecting the data required in 23 CFR 680.112. Joint Office users can view
      data submittals from Direct Recipients and their Subrecipients/Contractors and view stations in EV-ChART.
    </>
  );

  const drSummaryBox = (
    <>
      EV-ChART is the centralized hub for collecting the data required in 23 CFR 680.112. A Direct Recipient can either
      submit data themselves or designate a subrecipient or contractor to upload data on behalf of them. Follow the
      steps shown below to submit data to the EV-ChART.
    </>
  );

  const joetMainContent = (
    <div className="details-container">
      <h4 className="content-title"> Data Submittals </h4>
      <div className="content">
        The Joint Office can view the data submitted by Direct Recipients or Subrecipients/Contractors on behalf of the
        Direct Recipients. Data submittals are organized into nine modules that comprise the data required in 23 CFR
        680.112.
      </div>
      <Button
        type="button"
        className="joet-home-button"
        onClick={() => {
          navigate(ROUTE_MODULE_DATA, {
            state: {
              startTab: "submitted",
            },
          });
        }}
      >
        View Data Submittals
      </Button>
    </div>
  );

  const ffSubmitSRData = (
    <>
      <p className="dr-main-content-subheader">
        Review and approve/reject data uploaded by a subrecipient or a contractor:{" "}
      </p>
      <ol>
        <li>
          <Button
            type="button"
            className="link-styling"
            onClick={() => {
              navigate(ROUTE_MODULE_DATA, {
                state: {
                  startTab: "pending-approval",
                },
              });
            }}
          >
            Review the details of pending module data
          </Button>
        </li>
        <ol type="a" className="ff-submit-letter-ol">
          <li className="alpha-submit-ol-item"> Approve the data to finalize the submission </li>
          <li className="alpha-submit-ol-item">
            {" "}
            Reject the data and provide comments to notify subrecipients/contractors{" "}
          </li>
        </ol>
      </ol>
    </>
  );

  const drMainContent = (
    <div className="dr-main-content">
      <h4 className="dr-main-content-header">Before you submit data:</h4>
      <ol className="dr-before-submit">
        <li>
          The station you are reporting data for has been <a href={ROUTE_STATIONS}>registered into EV-ChART.</a>{" "}
        </li>
        <li>
          If you want to designate a Subrecipient or Contractor to submit data on behalf of your organization, add the
          subrecipient or contractor under the station using the{" "}
          <a href={ROUTE_STATION_REGISTRATION}>station registration page.</a>
        </li>
      </ol>
      <h4 className="dr-main-content-header">To submit data:</h4>

      {ffSubmitSRData}

      <p className="dr-main-content-subheader">Submit data directly by yourself:</p>
      <ol className={"submit-data-directly-list"}>
        <li className="submit-step-li">
          <div className="dr-submit-step">Upload New Module Data</div>
          <div className="dr-submit-step-helper">Begin by uploading a new data module to EV-ChART.</div>
          <div className="dr-upload-button">
            <Button
              type="button"
              className="upload-data-button"
              onClick={() => {
                navigate(ROUTE_MODULE_DATA, {
                  state: {
                    setUploadModalOpen: true,
                    startTab: "drafts",
                  },
                });
              }}
            >
              Upload New Module Data
            </Button>
          </div>
        </li>
        <li className="submit-step-li">
          <div className="dr-submit-step">Review the Module Data</div>
          <div className="dr-submit-step-helper">
            Once uploaded, ensure the data is formatted correctly in EV-ChART (refer to the Darta Input Template and the
            Data Format & Perparation Guide for additional support).
          </div>
        </li>
        <li className="submit-step-li">
          <div className="dr-submit-step">Submit the module data</div>
          <div className="dr-submit-step-helper">
            If the data is formatted correctly, select the "Submit Module Data" button - this is the final step to
            submit the data yourself.
          </div>
        </li>
      </ol>
    </div>
  );

  const drAuxillaryContent = (
    <div className="dr-auxillary-content">
      <h4 className="dr-auxillary-heading">Quick Links:</h4>
      {submissionTrackerFeatureFlag && (
        <Grid row>
          <Grid col={12} className="dr-quick-link">
            <div className="dr-quick-links-item">
              <Button
                type="button"
                className="link-styling"
                onClick={() =>
                  navigate(ROUTE_SUBMISSION_TRACKER, {
                    state: {
                      startTab: TabEnum.DRSubmissionTracker,
                    },
                  })
                }
              >
                Track submissions
              </Button>
            </div>
            <div className="dr-quick-links-helper">
              Track module submissions for each reporting deadline, by station
            </div>
          </Grid>
        </Grid>
      )}
      <Grid row>
        <Grid col={12} className="dr-quick-link">
          <div className="dr-quick-links-item">
            <Button
              type="button"
              className="link-styling"
              onClick={() => {
                navigate(ROUTE_MODULE_DATA, {
                  state: {
                    startTab: "drafts",
                  },
                });
              }}
            >
              View my draft module data
            </Button>
          </div>
          <div className="dr-quick-links-helper">Unsubmitted data that is still a work in progress</div>
        </Grid>
      </Grid>
      <Grid row>
        <Grid col={12} className="dr-quick-link">
          <div className="dr-quick-links-item">
            <Button
              type="button"
              className="link-styling"
              onClick={() => {
                navigate(ROUTE_MODULE_DATA, {
                  state: {
                    startTab: "pending-approval",
                  },
                });
              }}
            >
              View/review module data
            </Button>
          </div>
          <div className="dr-quick-links-helper">Data that is ready to be reviewed and submitted</div>
        </Grid>
      </Grid>
      <Grid row className="dr-quick-link">
        <Grid col={12}>
          <div className="dr-quick-links-item">
            <a href={ROUTE_STATIONS}>Manage stations</a>
          </div>
          <div className="dr-quick-links-helper">Charging stations associated with your organization</div>
        </Grid>
      </Grid>
      <Grid row className="dr-quick-link manage-users-link">
        <Grid col={12}>
          <div className="dr-quick-links-item">
            <a href={ROUTE_USERS}>Manage users</a>
          </div>
          <div className="dr-quick-links-helper">
            Users associated with your subrecipients/contractors and your organization
          </div>
        </Grid>
      </Grid>
    </div>
  );

  const joetAuxillaryContent = (
    <div className="auxillary-content-container">
      <h4 className="content-title">Stations</h4>
      <div className="content">
        The Joint Office can view the electric vehicle charging stations that are funded with Title 23 funds.
      </div>
      <Button
        type="button"
        className="joet-home-button"
        onClick={() => {
          navigate(ROUTE_STATIONS);
        }}
      >
        View Stations
      </Button>
    </div>
  );

  const joComingSoon = (
    <div className="jo-coming-soon">
      <h4 className="heading">Coming Soon</h4>
      <div>
        EV-ChART will provide even more tools to help you better understand the data that is being submitted by Direct
        Recipients and their Subrecipients/Contractors with analytics dashboards and reporting functionality.
      </div>
    </div>
  );

  const drResources = (
    <div className="dr-resources">
      <h4 className="resources-heading">Resources:</h4>
      <div>
        <Grid row className="dr-resources-link">
          <Grid col={12}>
            <a href="https://driveelectric.gov/evchart-user-guide" target="_blank" rel="noreferrer">
              User Manual
            </a>
          </Grid>
        </Grid>
        <Grid row className="dr-resources-link">
          <Grid col={12}>
            <a
              href="https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fdriveelectric.gov%2Ffiles%2Fev-chart-data-input-template.xlsx&wdOrigin=BROWSELINK"
              target="_blank"
              rel="noreferrer"
            >
              Data Input Template
            </a>
          </Grid>
        </Grid>
        <Grid row className="dr-resources-link format-prep-guide">
          <Grid col={12}>
            <a href="https://driveelectric.gov/files/ev-chart-data-guidance.pdf" target="_blank" rel="noreferrer">
              Format & Preparation Guide
            </a>
          </Grid>
        </Grid>
      </div>
    </div>
  );

  const summaryBoxMapping: ContentMapping = {
    joet: joetSummaryBox,
    "direct-recipient": drSummaryBox,
  };

  const mainContentMapping: ContentMapping = {
    joet: joetMainContent,
    "direct-recipient": drMainContent,
  };

  const auxillaryContentMapping: ContentMapping = {
    joet: joetAuxillaryContent,
    "direct-recipient": drAuxillaryContent,
  };

  function getSummaryBoxContent() {
    return summaryBoxMapping[userScope];
  }

  function getMainContent() {
    return mainContentMapping[userScope];
  }

  function getAuxillaryContent() {
    return auxillaryContentMapping[userScope];
  }

  return (
    <div id="home-page">
      <GridContainer>
        <h1 className="welcome-page-header">Welcome to EV-ChART!</h1>

        {(isDRUser() || isSRUser()) && showDueDateAlert && (
          <Alert className="due-date-banner" type="warning" headingLevel="h3" heading={dueDateHeading}>
            {dueDateText}
          </Alert>
        )}

        {!isSRUser() ? (
          <>
            <SummaryBox className="lets-get-started-summary">
              <SummaryBoxHeading headingLevel="h3">Let's get started!</SummaryBoxHeading>
              <SummaryBoxContent>{getSummaryBoxContent()}</SummaryBoxContent>
            </SummaryBox>
            <Grid row gap className="home-container">
              <Grid col={8}>
                <Grid>{getMainContent()}</Grid>
              </Grid>
              <Grid col={4}>
                <Grid>{getAuxillaryContent()}</Grid>
                {isDRUser() && <Grid className="resources-container">{drResources}</Grid>}
              </Grid>
            </Grid>
          </>
        ) : (
          <GettingStarted />
        )}

        {userScope === "joet" && (
          <Grid row gap>
            <Grid col={12}>
              <Grid className="details-container">{joComingSoon}</Grid>
            </Grid>
          </Grid>
        )}
      </GridContainer>
    </div>
  );
}

export default Home;
