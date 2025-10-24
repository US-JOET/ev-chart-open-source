/**
 * Module details view (for when single module selected).
 * @packageDocumentation
 **/
import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { useNavigate } from "react-router";

import {
  Actions,
  Alert,
  Button,
  Breadcrumb,
  BreadcrumbBar,
  BreadcrumbLink,
  Chip,
  Grid,
  GridContainer,
  StepIndicator,
  StepIndicatorStep,
  SummaryBox,
  SummaryBoxContent,
  SummaryBoxHeading,
  Spinner,
} from "evchartstorybook";

import { ModuleTwoHeaders, ModuleTwoDatum } from "../../interfaces/ModuleData/module-two-interface";
import { ModuleThreeDatum, ModuleThreeHeaders } from "../../interfaces/ModuleData/module-three-interface";
import { ModuleFourDatum, ModuleFourHeaders } from "../../interfaces/ModuleData/module-four-interface";
import { ModuleFiveHeaders, ModuleFiveDatum } from "../../interfaces/ModuleData/module-five-interface";
import { ModuleSixHeaders, ModuleSixDatum } from "../../interfaces/ModuleData/module-six-interface";
import { ModuleSevenHeaders, ModuleSevenDatum } from "../../interfaces/ModuleData/module-seven-interface";
import { ModuleEightHeaders, ModuleEightDatum } from "../../interfaces/ModuleData/module-eight-interface";
import { ModuleNineHeaders, ModuleNineDatum } from "../../interfaces/ModuleData/module-nine-interface";

import { isAdmin, isDRUser, isSRUser } from "../../utils/authFunctions";
import { FeatureFlagEnum, getFeatureFlagValue, getFeatureFlagList } from "../../utils/FeatureToggle";
import { getScope } from "../../utils/getJWTInfo";
import { PATH_MODULE_DATA, PATH_MODULE_DECISION, PATH_MODULE_DETAILS } from "../../utils/pathConstants";
import {
  ROUTE_HISTORY,
  ROUTE_HOME,
  ROUTE_MODULE,
  ROUTE_MODULE_DATA,
  ROUTE_NOT_AUTHORIZED,
  ROUTE_NOT_FOUND,
} from "../../utils/routeConstants";

import { HistoryLogTable } from "../../components/HistoryLog/HistoryLog";
import ApproveModal from "../../components/Modals/ApproveModal/ApproveModal";
import CSVDownloadModal from "../../components/Modals/CSVDownloadModal/CSVDownloadModal";
import ImportModal from "../../components/Modals/ImportModal/ImportModal";
import RejectModal from "../../components/Modals/RejectModuleModal/RejectModal";
import RemoveConfirmationModal from "../../components/Modals/RemoveConfirmationModal/RemoveConfirmation";
import SubmissionModal from "../../components/Modals/SubmissionModal/SubmissionModal";
import { ModuleDetailsTable } from "../../components/ModuleDetailsTable/ModuleDetailsTable";

import "./ModuleDetails.css";

interface ModuleInfo {
  module_name: string;
  year: string;
  submission_type: string;
  dr_id: string;
  updated_on: string;
  updated_by: string;
  upload_id: string;
  sr_id: string;
}

interface DecisionDetailsInfo {
  decision: string;
  decision_explanation: string;
  decision_explanation_str_one: string;
  decision_explanation_str_two: string;
  decision_explanation_str_three: string;
  decision_date: string;
  reviewer: string;
  comments: string;
}

export const ModuleDetails: React.FC = (): React.ReactElement => {
  /**
   * Method for changing the location / route
   */
  const navigate = useNavigate();
  const { state } = useLocation();

  /**
   * Get the api and base url from the environment variables
   */
  const API_URL = import.meta.env.VITE_API_URL;
  const BASE_URL = import.meta.env.VITE_PUBLIC_URL;

  /**
   * Get access and id token for endpoint authorization
   */
  const id_token = localStorage.getItem("id_token");

  /**
   * Feature flag management
   */
  const [removeModuleFeatureFlag, setRemoveModuleFeatureFlag] = useState(false);
  useEffect(() => {
    getFeatureFlagList().then((results) => {
      setRemoveModuleFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.RemoveModule));
    });
  }, []);

  /**
   * Get the user scope
   */
  const recipientType = getScope();

  /**
   * Split the url to see which module we're loading
   */
  const urlParts = window.location.href.split("/");

  /**
   * Get the upload id of the url to load
   */
  const uploadId = urlParts[4];

  /**
   * State variable for module status
   */
  const [moduleStatus, setModuleStatus] = useState<string>("");

  /**
   * State variable for module details
   */
  const [moduleDetails, setModuleDetails] = useState<ModuleInfo>({
    module_name: "",
    year: "",
    submission_type: "",
    dr_id: "",
    updated_on: "",
    updated_by: "",
    upload_id: "",
    sr_id: "",
  });

  /**
   * State variable for module headers
   */
  const [moduleHeaders, setModuleHeaders] = useState<
    | undefined
    | ModuleTwoHeaders
    | ModuleThreeHeaders
    | ModuleFourHeaders
    | ModuleFiveHeaders
    | ModuleSixHeaders
    | ModuleSevenHeaders
    | ModuleEightHeaders
    | ModuleNineHeaders
  >();

  /**
   * State variable for module data
   */
  const [moduleData, setModuleData] = useState<
    | undefined
    | Array<ModuleTwoDatum>
    | Array<ModuleThreeDatum>
    | Array<ModuleFourDatum>
    | Array<ModuleFiveDatum>
    | Array<ModuleSixDatum>
    | Array<ModuleSevenDatum>
    | Array<ModuleEightDatum>
    | Array<ModuleNineDatum>
  >();

  /**
   * State variable for the upload success banner when redirected from drafts table
   */
  const [uploadSuccessBanner, setUploadSuccessBanner] = useState(false);

  /**
   * State variable for the submit data modal for when it's a draft
   */
  const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
  const [isApproveModalOpen, setApproveModalOpen] = useState(false);
  const [isRejectModalOpen, setRejectModalOpen] = useState(false);
  const [isCSVDownloadModalOpen, setCSVDownloadModalOpen] = useState(false);
  const [isHistoryLogView, setIsHistoryLogView] = useState(false);
  const [isRemoveConfirmationModalOpen, setIsRemoveConfirmationModalOpen] = useState(false);
  const [isModuleDataLoading, setIsModuleDataLoading] = useState(true);
  const [isModuleDetailsLoading, setIsModuleDetailsLoading] = useState(true);

  /**
   * State variable for decision details
   */
  const [decisionDetails, setDecisionDetails] = useState<DecisionDetailsInfo>({
    decision: "",
    decision_explanation: "",
    decision_explanation_str_one: "",
    decision_explanation_str_two: "",
    decision_explanation_str_three: "",
    decision_date: "",
    reviewer: "",
    comments: "",
  });

  /**
   * State variable for the data over 1000 rows
   */
  const [over1000Rows, setOver1000Rows] = useState(false);

  /**
   * State variable for open import modal
   */
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);

  /**
   * Functions to open and close the import modal
   */
  const openImportModal = () => {
    setIsImportModalOpen(true);
  };
  const closeImportModal = () => {
    setIsImportModalOpen(false);
  };

  /**
   * Functions to open and close the submit modal with relevant data
   */
  const openSubmitModal = () => {
    setIsSubmitModalOpen(true);
  };
  const closeSubmitModal = () => {
    setIsSubmitModalOpen(false);
  };

  /**
   * Functions to open and close approval modal with relevant data
   */
  const openApproveModal = () => {
    setApproveModalOpen(true);
  };
  const closeApproveModal = () => {
    setApproveModalOpen(false);
  };

  /**
   * Functions to open and close reject modal with relevant data
   */
  const openRejectModal = () => {
    setRejectModalOpen(true);
  };
  const closeRejectModal = () => {
    setRejectModalOpen(false);
  };

  /**
   * Functions to open and close the CSV download modal
   */
  const openCSVDownloadModal = () => {
    setCSVDownloadModalOpen(true);
  };
  const closeCSVDownloadModal = () => {
    setCSVDownloadModalOpen(false);
  };

  /**
   * Functions to open and close the remove confirmation modal
   */
  const openRemoveConfirmationModal = () => {
    setIsRemoveConfirmationModalOpen(true);
  };
  const closeRemoveConfirmationModal = () => {
    setIsRemoveConfirmationModalOpen(false);
  };

  /**
   * Check to see if state from previous page exists indicating is a new upload
   */
  useEffect(() => {
    if (state && state.importSuccess) {
      setUploadSuccessBanner(true);
    }
  }, []);

  /**
   * Check if url indicates the history log should be shown
   */
  useEffect(() => {
    if (urlParts[5] === "history") {
      setIsHistoryLogView(true);
    }
  }, []);

  /**
   * If the module is approved or rejected, get the decision details
   */
  useEffect(() => {
    if (isApproved() || isRejected()) {
      fetch(`${API_URL}${PATH_MODULE_DECISION}?upload_id=${uploadId}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `${id_token}`,
        },
      })
        .then((response) => {
          if (response.ok) {
            return response.json();
          } else {
            throw response;
          }
        })
        .then((data) => {
          let decision_explanation_str_one = "",
            decision_explanation_str_two = "",
            decision_explanation_str_three = "";
          // Rejected char placement
          const rej = data.decision_explanation.search("rejected");
          // Approved char placement
          const appr = data.decision_explanation.search("approved");
          // Check if rejected is in the decision explanation
          if (rej !== -1) {
            decision_explanation_str_one = data.decision_explanation.substring(0, rej);
            decision_explanation_str_two = data.decision_explanation.substring(rej, rej + 8);
            decision_explanation_str_three = data.decision_explanation.substring(
              rej + 8,
              data.decision_explanation.length,
            );
          }
          // Check if approved is in the decision explanation
          if (appr !== -1) {
            decision_explanation_str_one = data.decision_explanation.substring(0, appr);
            decision_explanation_str_two = data.decision_explanation.substring(appr, appr + 8);
            decision_explanation_str_three = data.decision_explanation.substring(
              appr + 8,
              data.decision_explanation.length,
            );
          }
          setDecisionDetails({
            decision: data.decision,
            decision_explanation: data.decision_explanation,
            decision_explanation_str_one: decision_explanation_str_one,
            decision_explanation_str_two: decision_explanation_str_two,
            decision_explanation_str_three: decision_explanation_str_three,
            decision_date: data.decision_date,
            reviewer: data.reviewer,
            comments: data.comments === "" ? "N/A" : data.comments,
          });
        })
        .catch((err) => {
          const errorCode = err.status;
          if (errorCode === 403) {
            navigate(ROUTE_NOT_AUTHORIZED);
          }
          if (errorCode === 400) {
            navigate(ROUTE_NOT_FOUND);
          }
        });
    }
  }, [moduleStatus]);

  /**
   * Get the module details
   */
  useEffect(() => {
    const headersAPI: any = {
      Authorization: id_token,
      upload_id: uploadId,
    };

    fetch(`${API_URL}${PATH_MODULE_DETAILS}`, {
      method: "GET",
      headers: headersAPI,
    })
      .then((response) => {
        if (response.ok) {
          return response.json();
        } else {
          throw response;
        }
      })
      .then((data) => {
        if (data[0] !== undefined) {
          setModuleDetails({
            module_name: data[0].module_name,
            year: data[0].year,
            submission_type: data[0].module_frequency,
            dr_id: data[0].direct_recipient,
            updated_on: data[0].updated_on,
            updated_by: data[0].updated_by,
            upload_id: data[0].upload_id,
            sr_id: data[0].sub_recipient,
          });
          setModuleStatus(data[0].submission_status);
        }
      })
      .catch((err) => {
        const errorCode = err.status;
        if (errorCode === 403) {
          navigate(ROUTE_NOT_AUTHORIZED);
        }
        if (errorCode === 400) {
          navigate(ROUTE_NOT_FOUND);
        }
      })
      .finally(() => setIsModuleDetailsLoading(false));
  }, []);

  /**
   * Get the module data
   */
  useEffect(() => {
    const headersAPI: any = {
      Authorization: `${id_token}`,
      upload_id: uploadId,
      download: false,
    };
    fetch(`${API_URL}${PATH_MODULE_DATA}`, {
      method: "GET",
      headers: headersAPI,
    })
      .then((response) => {
        if (response.ok) {
          return response.json();
        } else {
          throw response;
        }
      })
      .then((data) => {
        setModuleHeaders(data.headerText);
        setModuleData(data.data);
        setOver1000Rows(data.truncated ? true : false);
      })
      .catch((err) => {
        const errorCode = err.status;
        if (errorCode === 403) {
          navigate(ROUTE_NOT_AUTHORIZED);
        }
        if (errorCode === 400) {
          navigate(ROUTE_NOT_FOUND);
        }
      })
      .finally(() => setIsModuleDataLoading(false));
  }, []);

  /**
   * Breadcrumb bar for page
   * @returns the base breadcrumb bar
   */
  const BaseBreadCrumb = (): React.ReactElement => (
    <>
      <Breadcrumb>
        <BreadcrumbLink href={`${BASE_URL}${ROUTE_HOME}`}>
          <span>Home</span>
        </BreadcrumbLink>
      </Breadcrumb>
      <Breadcrumb>
        <BreadcrumbLink href={`${BASE_URL}${ROUTE_MODULE_DATA}`}>
          <span>Module Data</span>
        </BreadcrumbLink>
      </Breadcrumb>
    </>
  );

  /**
   * Breadcrumb bar for page
   * @returns breadcrumb if viewing module data
   */
  const ModuleDetailsBreadCrumb = (): React.ReactElement => (
    <BreadcrumbBar>
      {BaseBreadCrumb()}
      <Breadcrumb current>
        <span>{moduleDetails["module_name"]}</span>
      </Breadcrumb>
    </BreadcrumbBar>
  );

  /**
   * Breadcrumb bar for page
   * @returns breadcrumb if viewing history log
   */
  const ModuleDetailsHistoryBreadCrumb = (): React.ReactElement => (
    <BreadcrumbBar>
      {BaseBreadCrumb()}
      <Breadcrumb>
        <BreadcrumbLink href={`${BASE_URL}${ROUTE_MODULE}/${uploadId}`}>
          <span>{moduleDetails["module_name"]}</span>
        </BreadcrumbLink>
      </Breadcrumb>
      <Breadcrumb current>
        <span>History Log</span>
      </Breadcrumb>
    </BreadcrumbBar>
  );

  /**
   * Function to return the styled chip depending on module status
   * @param moduleStatus the status of the module
   * @returns the styled chip
   */
  const ModuleChip = ({ moduleStatus }: { moduleStatus: string }): React.ReactElement => {
    let moduleChip: React.ReactElement;
    switch (moduleStatus.toUpperCase()) {
      case "DRAFT":
      default:
        moduleChip = <Chip type="info">Draft</Chip>;
        break;
      case "PENDING":
        moduleChip = <Chip type="warning">Pending Approval</Chip>;
        break;
      case "SUBMITTED":
        moduleChip = <Chip type="success">Submitted</Chip>;
        break;
      case "APPROVED":
        moduleChip = <Chip type="success">Approved</Chip>;
        break;
      case "REJECTED":
        moduleChip = <Chip type="error">Rejected</Chip>;
        break;
    }
    return moduleChip;
  };

  /**
   * Series of functions to check for module status
   * @returns true if module status matches function caller
   */
  function isDraft() {
    return moduleStatus.toUpperCase() === "DRAFT";
  }
  function isPending() {
    return moduleStatus.toUpperCase() === "PENDING";
  }
  function isSubmitted() {
    return moduleStatus.toUpperCase() === "SUBMITTED";
  }
  function isApproved() {
    return moduleStatus.toUpperCase() === "APPROVED";
  }
  function isRejected() {
    return moduleStatus.toUpperCase() === "REJECTED";
  }

  function moduleActions() {
    return (
      <Grid row>
        <Grid col={12} className="module-data-header">
          <div className="module-data-text">
            <p>Module Data</p>
          </div>
        </Grid>
      </Grid>
    );
  }

  /**
   * Download as csv capability
   * @returns the download button
   */
  const DownloadDetails = () => {
    return (
      <Button type="button" onClick={() => setCSVDownloadModalOpen(true)}>
        Download as CSV
      </Button>
    );
  };

  /**
   * Remove module button
   * @returns the remove module button
   */
  const RemoveModuleData = () => {
    return (
      <Button type="button" onClick={() => openRemoveConfirmationModal()}>
        Remove
      </Button>
    );
  };

  /**
   * Opens the import data modal
   * @returns the upload button
   */
  const UploadModuleData = () => {
    return (
      <Button type="button" onClick={openImportModal}>
        Upload Module Data
      </Button>
    );
  };

  /**
   * Redirects to the history log view
   * @param id the uuid of the current module
   * @returns the view history log button
   */
  const ViewHistoryLog = (id: string) => {
    return (
      <Button type="button" onClick={() => (window.location.href = `${ROUTE_MODULE}/${id}${ROUTE_HISTORY}`)}>
        View History Log
      </Button>
    );
  };

  /**
   * Get the available actions for the dropdown menu
   * @returns the list of available actions
   */
  const getActions = () => {
    const actions = [
      {
        name: "Download",
        component: DownloadDetails(),
      },
      {
        name: "ViewHistoryLog",
        component: ViewHistoryLog(uploadId),
      },
    ];
    if (isRejected()) {
      actions.push({
        name: "UploadModuleData",
        component: UploadModuleData(),
      });
    }

    /**
     * SR admins can remove Rejected modules.
     * DR and SR admins can remove Draft modules.
     */
    if (((isRejected() && isSRUser()) || isDraft()) && removeModuleFeatureFlag) {
      actions.push({
        name: "RemoveModuleData",
        component: RemoveModuleData(),
      });
    }
    return actions;
  };

  /**
   * Sub recipient view of module details
   * @returns the summary info
   */
  function halfWidthSummaryBox() {
    return (
      <Grid col={5}>
        <div className="module-details-gray-bg">
          <div className="module-details-details">
            <h3 className="module-details-header" style={{ margin: 0 }}>
              Module Details
            </h3>
            <div className="module-details-field">
              <p className="module-details-label">Reporting Year:</p>
              <p>{moduleDetails["year"]}</p>
            </div>
            <div className="module-details-field">
              <p className="module-details-label">Direct Recipient:</p>
              <p>{moduleDetails["dr_id"]}</p>
            </div>
            <div className="module-details-field">
              <p className="module-details-label">Type:</p>
              <p>{moduleDetails["submission_type"]}</p>
            </div>
            <div className="module-details-field">
              <p className="module-details-label">{isDraft() ? "Uploaded On:" : "Updated On:"}</p>
              <p>{moduleDetails["updated_on"]}</p>
            </div>
            <div className="module-details-field">
              <p className="module-details-label">{isDraft() ? "Uploaded By:" : "Updated By:"}</p>
              <p>{moduleDetails["updated_by"]}</p>
            </div>
            <div className="module-details-field">
              <p className="module-details-label">Upload ID:</p>
              <p>{moduleDetails["upload_id"]}</p>
            </div>
          </div>
        </div>
      </Grid>
    );
  }

  /**
   * View available to sub recipients to outline module step status
   * @returns the step indicator component
   */
  function StepIndicatorInfo() {
    return (
      <Grid col={7}>
        <div className="module-details-gray-bg">
          <div className="module-details-submission-status">
            <h3 style={{ margin: 0, paddingBottom: "66px" }}>Submission Status</h3>
            <StepIndicator showLabels={true} counters="small" className="submission-status-steps">
              <StepIndicatorStep
                label="Draft"
                status={isDraft() ? "current" : "complete"}
                className="submission-status-step"
              ></StepIndicatorStep>
              <StepIndicatorStep
                label="Pending Approval"
                status={isDraft() ? "incomplete" : isPending() ? "current" : "complete"}
                className="submission-status-step"
              ></StepIndicatorStep>
              <StepIndicatorStep
                label={isRejected() ? "Rejected" : "Approved"}
                status={
                  isDraft()
                    ? "incomplete"
                    : isPending()
                      ? "incomplete"
                      : isSubmitted() || isApproved()
                        ? "complete"
                        : "incomplete"
                }
                className={
                  isRejected() ? "submission-status-step submission-status-step-rejected" : "submission-status-step"
                }
              ></StepIndicatorStep>
            </StepIndicator>
          </div>
        </div>
      </Grid>
    );
  }

  /**
   * Direct recipient component that outlines module summary
   * @returns the full width details component
   */
  function fullWidthSummaryBox() {
    return (
      <Grid col={12}>
        <div className="module-details-gray-bg">
          <div className="dr-module-details-details">
            <h3 className="module-details-header" style={{ margin: 0 }}>
              Module Details
            </h3>
            <Grid row gap className="dr-module-details-row">
              <Grid col={3}>
                <div className="dr-module-details-field">
                  <p className="module-details-label">Reporting Year</p>
                  <p>{moduleDetails["year"]}</p>
                </div>
              </Grid>
              <Grid col={3}>
                <div className="dr-module-details-field">
                  <p className="module-details-label">Direct Recipient</p>
                  <p>{moduleDetails["dr_id"]}</p>
                </div>
              </Grid>
              <Grid col={3}>
                <div className="dr-module-details-field">
                  <p className="module-details-label">{isDraft() ? "Uploaded On" : "Updated On"}</p>
                  <p>{moduleDetails["updated_on"]}</p>
                </div>
              </Grid>
              <Grid col={3}>
                <div className="dr-module-details-field">
                  <p className="module-details-label">Upload ID</p>
                  <p>{moduleDetails["upload_id"]}</p>
                </div>
              </Grid>
            </Grid>
            <Grid row gap>
              <Grid col={3}>
                <div className="dr-module-details-field">
                  <p className="module-details-label">Type</p>
                  <p>{moduleDetails["submission_type"]}</p>
                </div>
              </Grid>
              <Grid col={3}>
                <div className="dr-module-details-field">
                  <p className="module-details-label">Subrecipient/Contractor</p>
                  <p>{moduleDetails["sr_id"]}</p>
                </div>
              </Grid>
              <Grid col={3}>
                <div className="dr-module-details-field">
                  <p className="module-details-label">{isDraft() ? "Uploaded By" : "Updated By"}</p>
                  <p>{moduleDetails["updated_by"]}</p>
                </div>
              </Grid>
            </Grid>
          </div>
        </div>
      </Grid>
    );
  }

  /**
   * For approved or rejected modules, the direct recipient decision and feedback
   * @returns the decision details
   */
  function decisionDetailsBox(): React.ReactNode {
    return (
      <SummaryBox className="decision-details-container">
        <SummaryBoxHeading headingLevel="h3" className="decision-details-header">
          Direct Recipient Feedback
        </SummaryBoxHeading>
        <SummaryBoxContent>
          <ul>
            <li>
              <div className="decision-details-field">
                <p className="decision-details-label">Decision: </p>
                <span>
                  {decisionDetails.decision_explanation_str_one} <u>{decisionDetails.decision_explanation_str_two}</u>{" "}
                  {decisionDetails.decision_explanation_str_three}
                </span>
              </div>
            </li>
            <li>
              <div className="decision-details-field">
                <p className="decision-details-label">Decision Date: </p>
                <span>{decisionDetails.decision_date}</span>
              </div>
            </li>
            <li>
              <div className="decision-details-field">
                <p className="decision-details-label">Reviewed By: </p>
                <span>{decisionDetails.reviewer}</span>
              </div>
            </li>
            <li>
              <div className="decision-details-field">
                <p className="decision-details-label">Feedback from Reviewer: </p>
                <span id="decisionDetailsComments">{decisionDetails.comments}</span>
              </div>
            </li>
          </ul>
        </SummaryBoxContent>
      </SummaryBox>
    );
  }

  /**
   * History log view
   * @returns the history log page header
   */
  function pageHeader() {
    const historyView = (
      <>
        <Grid row>
          <Grid col={12} style={{ display: "flex", alignItems: "center" }}>
            <h1>History Log</h1>
          </Grid>
        </Grid>
        <Grid row>
          <Grid col={12}>
            <h2 className="history-log-view-module-name">{moduleDetails["module_name"]}</h2>
          </Grid>
        </Grid>
      </>
    );

    const getModuleHeaderClassName = () => {
      let className = "module-header-name";
      if (isSubmitted() || isApproved() || isRejected()) {
        className += "-no-max";
      }
      return className;
    };

    const moduleView = (
      <>
        <Grid row gap>
          <Grid col={12}>
            <div className="module-details-header-container">
              <h1 className={getModuleHeaderClassName()}>{moduleDetails["module_name"]}</h1>
              <div className="module-header-chip">{moduleStatus && <ModuleChip moduleStatus={moduleStatus} />}</div>
              {isDraft() && (
                <div className="submit-module-data-button">
                  <Button type="button" onClick={() => openSubmitModal()}>
                    Submit
                  </Button>
                  <div className="module-details-actions-button">
                    <Actions
                      item={{
                        options: getActions(),
                      }}
                    />
                  </div>
                </div>
              )}
              {isRejected() && (isSRUser() || isDRUser()) && (
                <div className="rej-header-button module-details-actions-button">
                  <Actions
                    item={{
                      options: getActions(),
                    }}
                  />
                </div>
              )}
              {isDRUser() && isPending() && isAdmin() && (
                <div id="moduleButtons">
                  <Button
                    type="button"
                    outline
                    id="rejectModuleButton"
                    onClick={() => {
                      openRejectModal();
                    }}
                  >
                    Reject
                  </Button>
                  <Button
                    type="button"
                    id="approveModuleButton"
                    onClick={() => {
                      openApproveModal();
                    }}
                  >
                    Approve
                  </Button>
                </div>
              )}
            </div>
          </Grid>
        </Grid>
      </>
    );

    return isHistoryLogView ? historyView : moduleView;
  }

  return (
    <div className="module-details">
      <div>
        <GridContainer>
          {!isHistoryLogView ? <ModuleDetailsBreadCrumb /> : <ModuleDetailsHistoryBreadCrumb />}
        </GridContainer>
      </div>
      <div id="moduleDetails">
        <div className="usa-section" style={{ paddingTop: 0 }}>
          <GridContainer>
            {pageHeader()}
            <Grid row>
              <Grid col={12}>
                {isDraft() && (
                  <Alert
                    type="info"
                    headingLevel="h3"
                    className="draft-banner"
                    heading={"This module data is a draft and has not yet been submitted."}
                  ></Alert>
                )}
                {uploadSuccessBanner && (
                  <Alert
                    type="info"
                    headingLevel="h3"
                    className="upload-success-banner"
                    heading={
                      recipientType === "direct-recipient"
                        ? "Your module data is ready to be submitted"
                        : "Your module data is ready to be submitted for review"
                    }
                  >
                    Your draft module data was uploaded successfully
                  </Alert>
                )}
              </Grid>
            </Grid>
            {!isDraft() && (isDRUser() || isSRUser()) && isAdmin() && !isHistoryLogView && (
              <Grid row>
                <Grid col={12} className="view-history-log-container">
                  <Button
                    type="button"
                    unstyled
                    id="viewHistoryLogButton"
                    className="view-history-unstyled-button"
                    onClick={() => (window.location.href = `${ROUTE_MODULE}/${uploadId}${ROUTE_HISTORY}`)}
                  >
                    <p>View History Log</p>
                  </Button>
                </Grid>
              </Grid>
            )}
            {isModuleDetailsLoading ? (
              <div className="module-details-spinner">
                <Spinner />
              </div>
            ) : (
              <>
                {(decisionDetails.decision === "Approved" || decisionDetails.decision === "Rejected") &&
                  decisionDetailsBox()}
                {recipientType === "sub-recipient" && (
                  <Grid row gap>
                    {halfWidthSummaryBox()}
                    {StepIndicatorInfo()}
                  </Grid>
                )}
                {(recipientType === "direct-recipient" || recipientType === "joet") && (
                  <Grid row>{fullWidthSummaryBox()}</Grid>
                )}
              </>
            )}
            {over1000Rows && !isHistoryLogView && (
              <Grid row>
                <Grid col={12}>
                  <Alert
                    className="partial-data-banner"
                    type="warning"
                    headingLevel="h3"
                    heading="Viewing partial data"
                  >
                    <>
                      <div>
                        This data set contains more than 1,000 rows of data. You are viewing the first 1,000 rows. To
                        view the complete dataset download the CSV file.
                      </div>
                      <Button
                        type="button"
                        unstyled
                        id="bannerDownloadCSVButton"
                        className="module-details-unstyled-button"
                        onClick={() => openCSVDownloadModal()}
                      >
                        <p>Download as CSV</p>
                      </Button>
                    </>
                  </Alert>
                </Grid>
              </Grid>
            )}
            {isHistoryLogView ? (
              <>
                <HistoryLogTable />
              </>
            ) : (
              <>
                {moduleActions()}
                {isModuleDataLoading ? (
                  <div className="pp-dashboard-spinner-container">
                    <div className="pp-dashboard-spinner">
                      <Spinner />
                    </div>
                  </div>
                ) : (
                  <div>
                    <Grid row>
                      <Grid col={12}>
                        <ModuleDetailsTable
                          moduleHeaders={moduleHeaders}
                          moduleData={moduleData}
                          openCSVModal={openCSVDownloadModal}
                        ></ModuleDetailsTable>
                      </Grid>
                    </Grid>
                  </div>
                )}
              </>
            )}
          </GridContainer>
          {isSubmitModalOpen && (
            <SubmissionModal
              onClose={closeSubmitModal}
              moduleName={moduleDetails["module_name"]}
              year={moduleDetails["year"]}
              directRecipient={moduleDetails["dr_id"]}
              moduleType={moduleDetails["submission_type"]}
              uploadId={moduleDetails["upload_id"]}
            />
          )}
          {isApproveModalOpen && (
            <ApproveModal
              onClose={closeApproveModal}
              moduleName={moduleDetails["module_name"]}
              year={moduleDetails["year"]}
              subrecipient={moduleDetails["sr_id"]}
              directRecipient={moduleDetails["dr_id"]}
              updatedOn={moduleDetails["updated_on"]}
              updatedBy={moduleDetails["updated_by"]}
              moduleType={moduleDetails["submission_type"]}
              uploadId={moduleDetails["upload_id"]}
            />
          )}
          {isRejectModalOpen && (
            <RejectModal
              onClose={closeRejectModal}
              moduleName={moduleDetails["module_name"]}
              year={moduleDetails["year"]}
              subrecipient={moduleDetails["sr_id"]}
              directRecipient={moduleDetails["dr_id"]}
              updatedOn={moduleDetails["updated_on"]}
              updatedBy={moduleDetails["updated_by"]}
              moduleType={moduleDetails["submission_type"]}
              uploadId={moduleDetails["upload_id"]}
            />
          )}
          {isCSVDownloadModalOpen && (
            <CSVDownloadModal apiPath="data" onClose={closeCSVDownloadModal} uploadId={uploadId} />
          )}
          {isImportModalOpen && <ImportModal onClose={closeImportModal} />}
          {isRemoveConfirmationModalOpen && (
            <RemoveConfirmationModal
              onClose={closeRemoveConfirmationModal}
              moduleName={moduleDetails.module_name}
              year={moduleDetails.year}
              subRecipient={null}
              moduleType={moduleDetails.submission_type}
              moduleStatus={moduleStatus}
              updatedBy={moduleDetails.updated_by}
              uploadId={uploadId}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default ModuleDetails;
