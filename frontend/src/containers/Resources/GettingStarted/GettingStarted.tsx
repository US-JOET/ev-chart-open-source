/**
 * Getting started page.
 * @packageDocumentation
 **/
import React, { ReactNode, useEffect, useState } from "react";
import { useNavigate } from "react-router";

import classnames from "classnames";

import { Breadcrumb, BreadcrumbBar, BreadcrumbLink, Button, Grid, GridContainer, Table } from "evchartstorybook";

import { isAdmin, isDRUser, isSRUser } from "../../../utils/authFunctions";
import { FeatureFlagEnum, getFeatureFlagList, getFeatureFlagValue } from "../../../utils/FeatureToggle";
import {
  ROUTE_DIRECT_RECIPIENTS,
  ROUTE_HOME,
  ROUTE_MODULE_DATA,
  ROUTE_NETWORK_PROVIDERS,
  ROUTE_QUERY_DOWNLOAD,
  ROUTE_STATION_REGISTRATION,
  ROUTE_STATIONS,
  ROUTE_USERS,
} from "../../../utils/routeConstants";

import "./GettingStarted.css";

interface CardProps {
  className?: string;
  children: ReactNode;
}

export const Card: React.FC<CardProps & JSX.IntrinsicElements["div"]> = ({ className, children, ...defaultProps }) => {
  const cardClasses = classnames("evchart-card-container", className);
  return (
    <div className={cardClasses} {...defaultProps}>
      <div className="evchart-card">{children}</div>
    </div>
  );
};

function GettingStarted() {
  /**
   * Method for changing the location / route
   */
  const navigate = useNavigate();

  /**
   * Feature flag management
   */
  const [srAddsStationFeatureFlag, setSRAddsStationFeatureFlag] = useState(false);
  useEffect(() => {
    getFeatureFlagList().then((results) => {
      setSRAddsStationFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.SRAddsStation));
    });
  }, []);

  /**
   * Breadcrumb bar for page
   * @returns the breadcrumb bar
   */
  const DefaultBreadcrumb = (): React.ReactElement => (
    <BreadcrumbBar>
      <Breadcrumb>
        <BreadcrumbLink href={ROUTE_HOME}>
          <span>Home</span>
        </BreadcrumbLink>
      </Breadcrumb>
      <Breadcrumb current>
        <span>Getting Started</span>
      </Breadcrumb>
    </BreadcrumbBar>
  );

  /**
   * Set the columns for the table
   */
  const columnHeaders: { key: string; label: string }[] = [
    { key: "reporting_period", label: "Reporting Period" },
    { key: "data_modules", label: "Data Modules" },
    { key: "deadline", label: "Submission Deadline" },
  ];

  function getDRAdminQuickLinks() {
    return (
      <Card className="getting-started-card">
        <h3 className="getting-started-card__heading">Quick Links</h3>
        <div className="getting-started-card__link-container">
          <p>
            <a className="evchart-link" href={ROUTE_QUERY_DOWNLOAD}>
              Download module data
            </a>
          </p>
          <div className="getting-started-card__link-helper">Set custom parameters and download module data.</div>
        </div>
        <div className="getting-started-card__link-container">
          <div>
            <Button
              type="button"
              className="link-styling"
              onClick={() =>
                navigate(ROUTE_MODULE_DATA, {
                  state: {
                    startTab: "pending-approval",
                  },
                })
              }
            >
              Review pending module data
            </Button>
          </div>
          <div className="getting-started-card__link-helper">
            Approve or reject data submitted by subrecipients/contractors.
          </div>
        </div>
        <div className="getting-started-card__link-container">
          <p>
            <a className="evchart-link" href={ROUTE_STATIONS}>
              Manage stations
            </a>
          </p>
          <div className="getting-started-card__link-helper">
            Add and edit charging stations associated with your organization.
          </div>
        </div>
        <div className="getting-started-card__link-container">
          <p>
            <a className="evchart-link" href={ROUTE_USERS}>
              Manage users
            </a>
          </p>
          <div className="getting-started-card__link-helper">Add and edit users associated with your organization.</div>
        </div>
      </Card>
    );
  }

  function getDRViewerQuickLinks() {
    return (
      <Card className="getting-started-card">
        <h3 className="getting-started-card__heading">Quick Links</h3>
        <div className="getting-started-card__link-container">
          <p>
            <a className="evchart-link" href={ROUTE_QUERY_DOWNLOAD}>
              Download module data
            </a>
          </p>
          <div className="getting-started-card__link-helper">Set custom parameters and download module data.</div>
        </div>
        <div className="getting-started-card__link-container">
          <div>
            <Button
              type="button"
              className="link-styling"
              onClick={() =>
                navigate(ROUTE_MODULE_DATA, {
                  state: {
                    startTab: "pending-approval",
                  },
                })
              }
            >
              View module data
            </Button>
          </div>
          <div className="getting-started-card__link-helper">
            View individual module data files that have been approved/submitted.
          </div>
        </div>
        <div className="getting-started-card__link-container">
          <p>
            <a className="evchart-link" href={ROUTE_STATIONS}>
              View stations
            </a>
          </p>
          <div className="getting-started-card__link-helper">
            View charging stations associated with your organization.
          </div>
        </div>
        <div className="getting-started-card__link-container">
          <p>
            <a className="evchart-link" href={ROUTE_USERS}>
              View users
            </a>
          </p>
          <div className="getting-started-card__link-helper"> View users associated with your organization. </div>
        </div>
      </Card>
    );
  }

  function getSRAdminQuickLinks() {
    return (
      <Card className="getting-started-card">
        <h3 className="getting-started-card__heading">Quick Links</h3>
        <div className="getting-started-card__link-container">
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
            Submit draft module data
          </Button>
          <div className="getting-started-card__link-helper">
            View unsubmitted data that is still a work in progress.
          </div>
        </div>
        <div className="getting-started-card__link-container">
          <Button
            type="button"
            className="link-styling"
            onClick={() => {
              navigate(ROUTE_MODULE_DATA, {
                state: {
                  startTab: "submitted",
                },
              });
            }}
          >
            View approved module data
          </Button>

          <div className="getting-started-card__link-helper">
            View data that has been approved by direct recipients.
          </div>
        </div>
        <div className="getting-started-card__link-container">
          <div>
            <Button
              type="button"
              className="link-styling"
              onClick={() => {
                navigate(ROUTE_MODULE_DATA, {
                  state: {
                    startTab: "rejected",
                  },
                });
              }}
            >
              Remediate rejected modules
            </Button>
          </div>
          <div className="getting-started-card__link-helper">
            Review feedback in rejected module data to prepare for a new upload.
          </div>
        </div>
        <div className="getting-started-card__link-container">
          <p>
            <a className="evchart-link" href={ROUTE_STATIONS}>
              {srAddsStationFeatureFlag ? "Manage" : "View"} stations
            </a>
          </p>
          <div className="getting-started-card__link-helper">
            {srAddsStationFeatureFlag ? "Add and view" : "View"} charging stations associated with your organization.
          </div>
        </div>
        <div className="getting-started-card__link-container">
          <p>
            <a className="evchart-link" href={ROUTE_NETWORK_PROVIDERS}>
              View network providers
            </a>
          </p>
          <div className="getting-started-card__link-helper">
            Use the network provider names in each CSV file when submitting modules 2-9.
          </div>
        </div>
        <div className="getting-started-card__link-container">
          <p>
            <a className="evchart-link" href={ROUTE_DIRECT_RECIPIENTS}>
              View direct recipient IDs
            </a>
          </p>
          <div className="getting-started-card__link-helper">
            Use direct recipient IDs in each CSV file when uploading data for multiple direct recipients at once.
          </div>
        </div>
      </Card>
    );
  }

  function getBeforeSubmittingDataDRAdminInfo(): React.ReactNode {
    return (
      <Card className="getting-started-card submitting-data-card">
        <h3 className="getting-started-card__heading">Before Submitting Data</h3>
        <ol className="submitting-data-card__ol">
          <li className="submitting-data-card__li">
            Confirm the station you are reporting data for has been{" "}
            <a className="evchart-link" href={ROUTE_STATIONS}>
              added into EV-ChART
            </a>
          </li>
          <li className="submitting-data-card__li">
            If you want to designate a subrecipient/contractor to submit data on behalf of your organization,{" "}
            <a className="evchart-link" href={ROUTE_STATION_REGISTRATION}>
              authorize the subrecipient/ contractor
            </a>{" "}
            to submit data for a station (Step 2 in adding a station)
          </li>
        </ol>
        <h3 className="submitting-data-card__heading">Submitting Data</h3>

        <>
          <h4 className="submitting-data-card__subheading">
            Review and approve/reject data uploaded by a subrecipient/ contractor:
          </h4>
          <ol className="submitting-data-card__ol">
            <li className="submitting-data-card__li">
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
                Review the details of the submitted data
              </Button>
            </li>
            <li className="submitting-data-card__li">Approve or reject the submitted data</li>
            <ol type="a">
              <li className="submitting-data-card__li-helper">If you approve, that submission is finalized</li>
              <li className="submitting-data-card__li-helper">
                If you reject, provide feedback so the subrecipient/contractor may remediate issues and reupload new
                module data
              </li>
            </ol>
          </ol>
        </>

        <h4 className="submitting-data-card__subheading submitting-data-card__subheading--direct">
          Submit data directly by yourself:
        </h4>
        <ol className="submitting-data-card__ol">
          <li className="submitting-data-card__li">
            <div>Review the module data within the Data Input Template</div>
            <div className="submitting-data-card__li-helper">
              Ensure the data is formatted correctly in EV-ChART (refer to the EV-ChART Data Format and Preparation
              Guidance)
            </div>
          </li>
          <li className="submitting-data-card__li">
            <div>Upload new module data</div>
            <div className="submitting-data-card__li-helper">Uploading a new data module CSV file to EV-ChART</div>
            <div className="upload-data-button-container">
              <Button
                type="button"
                className="upload-data-button"
                onClick={() =>
                  navigate(ROUTE_MODULE_DATA, {
                    state: {
                      setUploadModalOpen: true,
                      startTab: "drafts",
                    },
                  })
                }
              >
                Upload New Module Data
              </Button>
            </div>
          </li>
          <li className="submitting-data-card__li">
            <div>Review draft before submitting</div>
            <div className="submitting-data-card__li-helper">
              Review and confirm data is displayed in EV-ChART as expected
            </div>
          </li>
          <li className="submitting-data-card__li">
            <div>Submit data</div>
            <div className="submitting-data-card__li-helper">
              After reviewing the draft, select the “Submit” button - this is the final step to submit data yourself
            </div>
          </li>
        </ol>
      </Card>
    );
  }

  function getBeforeSubmittingDataSRInfo(): React.ReactNode {
    return (
      <Card className="getting-started-card submitting-data-card">
        <h3 className="getting-started-card__heading">Before you submit data, confirm that:</h3>
        <ol className="submitting-data-card__ol">
          <li className="submitting-data-card__li">
            The station you are reporting data for has been{" "}
            <a className="evchart-link" href={ROUTE_STATIONS}>
              added into EV-ChART
            </a>{" "}
            and you are authorized by the direct recipient to submit data.{" "}
            {!srAddsStationFeatureFlag && "This can only be completed by the direct recipient."}
          </li>
        </ol>
        <h3 className="submitting-data-card__heading">To submit data:</h3>

        <ol className="submitting-data-card__ol">
          <li className="submitting-data-card__li">
            <div>Upload module data</div>
            <div className="upload-data-button-container">
              <Button
                type="button"
                className="upload-data-button"
                onClick={() =>
                  navigate(ROUTE_MODULE_DATA, {
                    state: {
                      setUploadModalOpen: true,
                      startTab: "drafts",
                    },
                  })
                }
              >
                Upload New Module Data
              </Button>
            </div>
          </li>
          <li className="submitting-data-card__li">
            <div>Submit the module data</div>
          </li>
          <li className="submitting-data-card__li">
            <div>Wait for direct recipient review</div>
          </li>
          <li className="submitting-data-card__li">
            <div>Submission finalized once approved</div>
            <ol type="a">
              <li className="submitting-data-card__li-helper">
                If module data is approved, that submission is finalized
              </li>
              <li className="submitting-data-card__li-helper">
                If module data is rejected, review feedback from the direct recipient, remediate issues, and reupload
                new module data
              </li>
            </ol>
          </li>
        </ol>
      </Card>
    );
  }

  function getSubmissionDeadlines() {
    return (
      <Card className="getting-started-card">
        <h3 className="getting-started-card__heading">Submission Deadlines</h3>
        <Table striped fullWidth bordered={false} className="submission-deadlines-table">
          <thead>
            <tr>
              {columnHeaders.map(({ key, label }) => (
                <th key={key} scope="col" data-testid={key}>
                  <div>{label}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody data-testid="submissionDeadlinesTable" className="submission-deadlines-table__tbody">
            <tr data-testid="submissionDeadlinesRow">
              <td>One Time</td>
              <td className="submission-deadlines-table__column-nowrap">
                <div>Module 1 (Station Location)</div>
                {isAdmin() && (
                  <div>
                    <a className="evchart-link" href={ROUTE_STATION_REGISTRATION}>
                      Add Station
                    </a>
                  </div>
                )}
              </td>
              <td>
                Must complete for each station upon its <b>operational date</b>
              </td>
            </tr>

            <tr data-testid="submissionDeadlinesRow">
              <td>One Time</td>
              <td className="submission-deadlines-table__column-nowrap">
                <div>Module 6 (Station Operator Identity)</div>
                <div>Module 8 (DER Information)</div>
                <div>Module 9 (Capital & Installation Costs)</div>
              </td>
              <td>
                <b>March 1</b>
              </td>
            </tr>
            <tr data-testid="submissionDeadlinesRow">
              <td>Annual</td>
              <td className="submission-deadlines-table__column-nowrap">
                <div>Module 5 (Maintenance Costs)</div>
                <div>Module 7 (Station Operator Program)</div>
              </td>
              <td>
                <b>March 1</b>
              </td>
            </tr>
            <tr data-testid="submissionDeadlinesRow">
              <td>Quarterly</td>
              <td className="submission-deadlines-table__column-nowrap">
                <div>Module 2 (Charging Sessions)</div>
                <div>Module 3 (Uptime)</div>
                <div>Module 4 (Outages)</div>
              </td>
              <td className="submission-deadlines-table__column-nowrap">
                <div>
                  Quarter 1 (Jan-Mar): <b>April 30</b>
                </div>
                <div>
                  Quarter 2 (Apr-Jun): <b>July 31</b>
                </div>
                <div>
                  Quarter 3 (Jul-Sep): <b>October 31</b>
                </div>
                <div>
                  Quarter 4 (Oct-Dec): <b>January 31</b>
                </div>
              </td>
            </tr>
          </tbody>
        </Table>
      </Card>
    );
  }

  function getGuidesAndTemplates() {
    return (
      <Card className="getting-started-card">
        <h3 className="getting-started-card__heading">Guides & Templates</h3>
        <p className="getting-started-card__link-container">
          <a
            className="evchart-link"
            href="https://driveelectric.gov/evchart-user-guide"
            target="_blank"
            rel="noreferrer"
          >
            EV-ChART User Manual
          </a>
        </p>
        <p className="getting-started-card__link-container">
          <a
            className="evchart-link"
            href="https://driveelectric.gov/files/ev-chart-data-guidance.pdf"
            target="_blank"
            rel="noreferrer"
          >
            Data Format and Preparation Guidance
          </a>
        </p>
        <p className="getting-started-card__link-container">
          <a
            className="evchart-link"
            href="https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fdriveelectric.gov%2Ffiles%2Fev-chart-data-input-template.xlsx&wdOrigin=BROWSELINK"
            target="_blank"
            rel="noreferrer"
          >
            Data Input Template
          </a>
        </p>
      </Card>
    );
  }

  /**
   * Function to retrieve the quick links
   * @returns the relevant quick links by org type
   */
  function getQuickLinks() {
    if (isDRUser()) {
      return isAdmin() ? getDRAdminQuickLinks() : getDRViewerQuickLinks();
    }
    return getSRAdminQuickLinks();
  }

  return (
    <div className="resources-getting-started">
      {isDRUser() && (
        <GridContainer>
          <DefaultBreadcrumb />
        </GridContainer>
      )}
      <div id="GettingStarted">
        <div className="usa-section" style={{ paddingTop: 0 }}>
          <GridContainer className={isSRUser() ? "full-wdith-getting-started" : "padded-width"}>
            <Grid row>
              <Grid col={isDRUser() ? 12 : 9}>
                <h1>{isDRUser() && "Getting Started"}</h1>
                {isDRUser() && (
                  <p>
                    EV-ChART is the centralized hub for collecting the data required in 23 CFR 680.112. As a direct
                    recipient
                    {isAdmin()
                      ? ", you can either submit data yourselves or authorize a subrecipient/contractor to upload data on your behalf"
                      : " viewer, you can view or download data within your organization."}
                  </p>
                )}
                {isSRUser() && (
                  <p>
                    EV-ChART is the centralized hub for collecting the data required in 23 CFR 680.112.
                    <br />
                    Follow the steps below to submit data to EV-ChART.
                  </p>
                )}
              </Grid>
            </Grid>
            <Grid row gap>
              <Grid col={8}>
                {getSubmissionDeadlines()}
                {isDRUser() && isAdmin() && getBeforeSubmittingDataDRAdminInfo()}
                {isSRUser() && getBeforeSubmittingDataSRInfo()}
              </Grid>
              <Grid col={4}>
                {getGuidesAndTemplates()}
                {getQuickLinks()}
              </Grid>
            </Grid>
          </GridContainer>
        </div>
      </div>
    </div>
  );
}

export default GettingStarted;
