/**
 * Landing page with tabs for viewing module uploads.
 * @packageDocumentation
 **/
import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { Tab, Tabs, TabsList, TabPanel } from "@mui/base";

import {
  Alert,
  Breadcrumb,
  BreadcrumbBar,
  BreadcrumbLink,
  Button,
  Grid,
  GridContainer,
  Spinner,
  SummaryBox,
  SummaryBoxContent,
  SummaryBoxHeading,
} from "evchartstorybook";

import { isSRUser, isDRUser, isJOUser, isAdmin } from "../../utils/authFunctions";
import { getOrgID, getScope } from "../../utils/getJWTInfo";
import { PATH_AUTHORIZATIONS, PATH_DRAFT_SUBMITTED } from "../../utils/pathConstants";
import { ROUTE_HOME } from "../../utils/routeConstants";

import DraftsTabTable from "../../components/DraftsTabTable/DraftsTabTable";
import ColumnDefinitionsModal from "../../components/Modals/ColumnDefinitionModal/ColumnDefinitions";
import CSVDownloadModal from "../../components/Modals/CSVDownloadModal/CSVDownloadModal";
import ErrorGuidanceModal from "../../components/Modals/ErrorGuidanceModal/ErrorGuidanceModal";
import ImportModal from "../../components/Modals/ImportModal/ImportModal";
import RemoveConfirmationModal from "../../components/Modals/RemoveConfirmationModal/RemoveConfirmation";
import SubmissionStatusModal from "../../components/Modals/SubmissionStatusModal/SubmissionStatusModal";
import SubmittalsTabTable from "../../components/SubmittalsTabTable/SubmittalsTabTable";

import "./ModuleData.css";

interface DraftModuleInfo {
  module_name: string;
  year: string;
  module_frequency: string;
  direct_recipient: string;
  submission_status: string;
  updated_on: string;
  updated_by: string;
  upload_id: string;
}

interface ModuleInfo {
  module_name: string;
  year: string;
  module_frequency: string;
  direct_recipient: string;
  sub_recipient: string;
  submission_status: string;
  updated_on: string;
  updated_by: string;
  upload_id: string;
}

interface SubmitDraftInfoInterface {
  showSubmitSuccessModal?: boolean;
  showApprovedSuccessModal?: boolean;
  showRejectedSuccessModal?: boolean;
  showConflictModal?: boolean;
  showUploadAsyncModal?: boolean;
  showRemoveSuccessAlert?: boolean;
  moduleName: string;
  moduleYear: string;
  moduleType: string;
  directRecipient: string;
  forceRefresh?: boolean;
}

/**
 * Function to get the banner text for submitted modules
 * @param stateInfo the state from the user navigating to the page
 * @returns the appropriate text for a submitted module banner
 */
export function getSubmitModuleSubtext(stateInfo: SubmitDraftInfoInterface) {
  /**
   * Determine the user type
   */
  const scope = getScope();

  /**
   * SR Messaging
   */
  const notifiedByEmail = " will be notified by email that ";
  const requiresApproval = " requires their approval for final submission.";

  /**
   * DR Messaging
   */
  const successSubmit = "You successfully submitted ";
  const onBehalf = " for ";
  const noFurtherAction = ". No further action is required.";

  /**
   * module info from state
   */
  const { moduleType, directRecipient, moduleName, moduleYear } = stateInfo;

  const moduleTypeText =
    moduleType === "Annual" ? ` for ${moduleYear}` : moduleType === "One-Time" ? "" : ` for ${moduleType}`;

  /**
   * return the appropriate text based on user type
   */
  if (scope === "sub-recipient") {
    return directRecipient + notifiedByEmail + moduleName + moduleTypeText + requiresApproval;
  } else {
    const submissionType = moduleType === "One-Time" ? ", a one-time submission," : moduleTypeText;
    return successSubmit + moduleName + submissionType + onBehalf + directRecipient + noFurtherAction;
  }
}

/**
 * Function to get the banner text for approved and rejected modules
 * @param stateInfo the state from the user navigating to the page
 * @param approve true if approval, false if rejection
 * @returns the appropriate text for the approved/rejected module banner
 */
export function getApprovedRejectedModuleSubtext(stateInfo: SubmitDraftInfoInterface, approve: boolean) {
  const willBeNotified = `The subrecipient/contractor will be notified by email of the ${approve ? "approval" : "rejection"} of `;
  const { moduleType, moduleName, moduleYear } = stateInfo;

  const typeSuffix =
    moduleType === "One-Time"
      ? ", a one-time submission."
      : ` for ${moduleType === "Annual" ? moduleYear : `${moduleType}, ${moduleYear}`}.`;

  return willBeNotified + moduleName + typeSuffix;
}

function ModuleData() {
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
   * Get the user scope and org id
   */
  const scope = getScope();
  const [orgID, setOrgID] = useState("");
  useEffect(() => {
    const jwtOrgID = getOrgID();
    if (jwtOrgID) {
      setOrgID(jwtOrgID);
    }
  }, []);

  /**
   * Set the state variables for the draft submittal info
   */
  const stateInfo: SubmitDraftInfoInterface = {
    showSubmitSuccessModal: state && state["showSubmitSuccessModal"] ? true : false,
    showApprovedSuccessModal: state && state["showApprovedSuccessModal"] ? true : false,
    showRejectedSuccessModal: state && state["showRejectedSuccessModal"] ? true : false,
    showConflictModal: state && state["showConflictModal"] ? true : false,
    showUploadAsyncModal: state && state["showUploadAsyncModal"] ? true : false,
    showRemoveSuccessAlert: state && state["showRemoveSuccessAlert"] ? true : false,
    moduleName: state && state["moduleName"] ? state["moduleName"] : "",
    moduleYear: state && state["moduleYear"] ? state["moduleYear"] : "",
    moduleType: state && state["moduleType"] ? state["moduleType"] : "",
    directRecipient: state && state["directRecipient"] ? state["directRecipient"] : "",
    forceRefresh: state && state["forceRefresh"] && localStorage.getItem("beenRefreshed") === null ? true : false,
  };

  /**
   * Force refresh the page if needed
   */
  if (stateInfo.forceRefresh) {
    localStorage.setItem("beenRefreshed", "true");
    window.scrollTo({ top: 0, behavior: "smooth" });
    navigate(0);
  }

  /**
   * State variables for modals
   */
  const [isImportModalOpen, setIsImportModalOpen] = useState(state && state.setUploadModalOpen ? true : false);
  const [isColumnDefinitionsModalOpen, setIsColumnDefinitionsModalOpen] = useState(false);
  const [isErrorGuidanceModalOpen, setIsErrorGuidanceModalOpen] = useState(false);
  const [isErrorDownloadModalOpen, setIsErrorDownloadModalOpen] = useState(false);
  const [isCSVDownloadModalOpen, setIsCSVDownloadModalOpen] = useState(false);
  const [isSubmissionStatusModalOpen, setIsSubmissionStatusModalOpen] = useState(false);
  const [isRemoveConfirmationModalOpen, setIsRemoveConfirmationModalOpen] = useState(false);
  const [isDraftDataLoading, setIsDraftDataLoading] = useState(true);
  const [isSubmittedDataLoading, setIsSubmittedDataLoading] = useState(true);

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
   * Functions to open and close the column definitions modal
   */
  const openColumnDefinitionsModal = () => {
    setIsColumnDefinitionsModalOpen(true);
  };
  const closeColumnDefinitionsModal = () => {
    setIsColumnDefinitionsModalOpen(false);
  };

  /**
   * Functions to open and close the error download modal
   */
  const openErrorDownloadModal = () => {
    setIsErrorDownloadModalOpen(true);
  };
  const closeErrorDownloadModal = () => {
    setIsErrorDownloadModalOpen(false);
  };

  /**
   * Functions to open and close the error guidance modal
   */
  const openErrorGuidanceModal = () => {
    setIsErrorGuidanceModalOpen(true);
  };
  const closeErrorGuidanceModal = () => {
    setIsErrorGuidanceModalOpen(false);
  };

  /**
   * Functions to open and close the CSV download modal
   */
  const openCSVDownloadModal = () => {
    setIsCSVDownloadModalOpen(true);
  };
  const closeCSVDownloadModal = () => {
    setIsCSVDownloadModalOpen(false);
  };

  /**
   * Function to close the remove module download modal
   */
  const closeRemoveModuleModal = () => {
    setIsRemoveConfirmationModalOpen(false);
  };

  /**
   * Functions to open and close the submission status modal
   */
  const openSubmissionStatusModal = () => {
    setIsSubmissionStatusModalOpen(true);
  };

  const closeSubmissionStatusModal = () => {
    setIsSubmissionStatusModalOpen(false);
  };

  /**
   * State variable to hold the data for module selected for removal
   */
  const [selectedRemoveModule, setSelectedRemoveModule] = useState<ModuleInfo>({
    module_name: "",
    year: "",
    module_frequency: "",
    direct_recipient: "",
    sub_recipient: "",
    submission_status: "",
    updated_on: "",
    updated_by: "",
    upload_id: "",
  });

  /**
   * Function called when module selected for removal
   * @param selectedToRemove the module that was selected for removal
   */
  const handleAction = (selectedToRemove: ModuleInfo) => {
    setSelectedRemoveModule(selectedToRemove);
    setIsRemoveConfirmationModalOpen(true);
  };

  /**
   * State variable to pass to the CSV download to set upload ID for the modal
   */
  const [currUploadId, setCurrUploadId] = useState("");

  /**
   * Function to set the current upload ID for the download CSV modal
   */
  const getCurrentUploadId = (id: string) => {
    setCurrUploadId(id);
  };

  /**
   * state variable to pass to the CSV download to set module Name for the modal
   */
  const [currModuleName, setCurrModuleName] = useState("");

  /**
   * Function to set the current module name for the download CSV modal
   */
  const getCurrentModuleName = (id: string) => {
    setCurrModuleName(id);
  };

  /**
   * Summary details for SR with no station authorization state variable
   */
  const [isAuthorizedToDR, setIsAuthorizedToDR] = useState(true);

  /**
   * State variable for current tab
   */
  const [currentTab, setCurrentTab] = useState(
    state && state.startTab ? state.startTab : isJOUser() || isSRUser() ? "all" : "pending-approval",
  );

  /**
   * Function to change the tab value
   */
  const setTabValue = (e: any) => {
    setCurrentTab(e.target.id);
  };

  /**
   * State variable for column defintions modal value
   */
  const [colDefModalValue, setColDefModalValue] = useState("");

  /**
   * Update the column definitions modal scope per updates to currentTab
   */
  useEffect(() => {
    let tableName = "";
    switch (currentTab) {
      case "drafts":
        isSRUser() ? (tableName = "sr_draft_data") : (tableName = "dr_draft_data");
        break;
      case "all":
      case "pending-approval":
      case "submitted":
      case "rejected":
      case "errors":
        isSRUser()
          ? isAdmin()
            ? (tableName = "sr_admin_submitted_data")
            : (tableName = "sr_viewer_submitted_data")
          : isDRUser()
            ? isAdmin()
              ? (tableName = "dr_admin_submitted_data")
              : (tableName = "dr_viewer_submitted_data")
            : (tableName = "jo_submitted_data");
        break;
    }

    setColDefModalValue(tableName);
  }, [currentTab]);

  /**
   * Check to see if data should be shown for SR
   */
  useEffect(() => {
    if (scope === "sub-recipient") {
      fetch(`${API_URL}${PATH_AUTHORIZATIONS}`, {
        method: "GET",
        headers: {
          Authorization: `${id_token}`,
        },
      })
        .then((response) => response.json())
        .then((data) => {
          setIsAuthorizedToDR(data);
        })
        .catch((err) => {
          console.log(err.message);
        });
    }
  }, []);

  /**
   * State variables for the draft and submitted data
   */
  const [pendingApproval, setPendingApproval] = useState<ModuleInfo[]>([]);
  const [noPendingApproval, setNoPendingApproval] = useState<number>(0);

  const [submitted, setSubmitted] = useState<ModuleInfo[]>([]);
  const [noSubmitted, setNoSubmitted] = useState<number>(0);

  const [rejected, setRejected] = useState<ModuleInfo[]>([]);
  const [noRejected, setNoRejected] = useState<number>(0);

  const [drafts, setDrafts] = useState<DraftModuleInfo[]>([]);
  const [noDrafts, setNoDrafts] = useState<number>(0);

  const [error, setError] = useState<ModuleInfo[]>([]);
  const [noError, setNoError] = useState<number>(0);

  /**
   * Get draft and submitted data
   */
  useEffect(() => {
    if (orgID) {
      // Fetch call for the draft applications
      fetch(`${API_URL}${PATH_DRAFT_SUBMITTED}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `${id_token}`,
          status: "draft",
        },
      })
        .then((response) => response.json())
        .then((data) => {
          setDrafts(data);
          setNoDrafts(data.length);
        })
        .catch((err) => {
          console.log(err.message);
        })
        .finally(() => setIsDraftDataLoading(false));
    }
  }, [orgID]);
  useEffect(() => {
    if (orgID) {
      // Fetch call for the submitted applications
      fetch(`${API_URL}${PATH_DRAFT_SUBMITTED}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `${id_token}`,
          status: "submitted",
        },
      })
        .then((response) => response.json())
        .then((data) => {
          const pendingApprovalData: any = [],
            submittedData: any = [],
            rejectedData: any = [],
            errorData: any = [];
          data.forEach((datum: any) => {
            if (datum.submission_status === "Pending") {
              pendingApprovalData.push(datum);
            } else if (datum.submission_status === "Submitted" || datum.submission_status === "Approved") {
              submittedData.push(datum);
            } else if (datum.submission_status === "Rejected") {
              rejectedData.push(datum);
            } else if (datum.submission_status === "Error") {
              errorData.push(datum);
            }
          });
          setPendingApproval(pendingApprovalData);
          setNoPendingApproval(pendingApprovalData.length);
          setSubmitted(submittedData);
          setNoSubmitted(submittedData.length);
          setRejected(rejectedData);
          setNoRejected(rejectedData.length);
          setError(errorData);
          setNoError(errorData.length);
        })
        .catch((err) => {
          console.log(err.message);
        })
        .finally(() => setIsSubmittedDataLoading(false));
    }
  }, [orgID]);

  /**
   * Information present to users when they have not been authorized to upload data by any organization yet
   * @returns summary box content
   */
  function summaryDetailsBox(): React.ReactNode {
    return (
      <SummaryBox className="no-authorization-container">
        <SummaryBoxHeading headingLevel="h3" className="no-authorization-header">
          Your organization is not yet authorized to submit data for stations
        </SummaryBoxHeading>
        <SummaryBoxContent className="no-authorization-body">
          To become authorized to submit data, please contact your direct recipient and ensure that you are an
          authorized subrecipient/contractor under the Station Registration page.
        </SummaryBoxContent>
      </SummaryBox>
    );
  }

  /**
   * Breadcrumb bar for page
   * @returns the breadcrumb bar
   */
  const DefaultBreadcrumb = (): React.ReactElement => (
    <BreadcrumbBar>
      <Breadcrumb>
        <BreadcrumbLink href={`${BASE_URL}${ROUTE_HOME}`}>
          <span>Home</span>
        </BreadcrumbLink>
      </Breadcrumb>
      <Breadcrumb current>
        <span>Module Data</span>
      </Breadcrumb>
    </BreadcrumbBar>
  );

  return (
    <div>
      <div>
        <GridContainer>
          <DefaultBreadcrumb />
        </GridContainer>
      </div>
      <GridContainer>
        {stateInfo.showSubmitSuccessModal && (
          <Grid row>
            <Grid col={12}>
              <Alert
                className="submit-draft-success-banner"
                type="success"
                headingLevel="h1"
                heading={
                  scope === "sub-recipient"
                    ? stateInfo.moduleName + " data submitted for review successfully"
                    : stateInfo.moduleName + " data submitted successfully"
                }
              >
                {getSubmitModuleSubtext(stateInfo)}
              </Alert>
            </Grid>
          </Grid>
        )}

        {stateInfo.showApprovedSuccessModal && (
          <Grid row>
            <Grid col={12}>
              <Alert
                className="approved-success-banner"
                type="success"
                headingLevel="h1"
                heading={stateInfo.moduleName + " data approved successfully"}
              >
                {getApprovedRejectedModuleSubtext(stateInfo, true)}
              </Alert>
            </Grid>
          </Grid>
        )}

        {stateInfo.showRejectedSuccessModal && (
          <Grid row>
            <Grid col={12}>
              <Alert
                className="rejected-success-banner"
                type="error"
                headingLevel="h1"
                heading={stateInfo.moduleName + " data rejected successfully"}
              >
                {getApprovedRejectedModuleSubtext(stateInfo, false)}
              </Alert>
            </Grid>
          </Grid>
        )}

        {stateInfo.showConflictModal && (
          <Grid row>
            <Grid col={12}>
              <Alert
                className="rejected-success-banner"
                type="error"
                headingLevel="h1"
                heading={stateInfo.moduleName + " data is duplicative and cannot be submitted."}
              >
                The file attempting submission contains previously submitted data. View the error report for details
                (column C).
              </Alert>
            </Grid>
          </Grid>
        )}
        {stateInfo.showUploadAsyncModal && (
          <Grid row>
            <Grid col={12}>
              <Alert
                className="async-upload-banner"
                type="info"
                headingLevel="h1"
                heading={stateInfo.moduleName + " data now uploading"}
              >
                You will be notified by email when upload/processing is complete and your module data is ready to
                submit.
              </Alert>
            </Grid>
          </Grid>
        )}

        {stateInfo.showRemoveSuccessAlert && (
          <Grid row>
            <Grid col={12}>
              <Alert
                className="submit-draft-success-banner"
                type="success"
                headingLevel="h1"
                heading="Data removed successfully"
              >
                This action cannot be undone, and the data module cannot be recovered.
              </Alert>
            </Grid>
          </Grid>
        )}

        <Grid row gap>
          <Grid col={9}>
            <h1 className="module-data-tabs-header">Module Data</h1>
          </Grid>
          {(isSRUser() || isDRUser()) && isAdmin() && (
            <Grid col={3}>
              <Button
                className="draft-page-header-button upload-module-data"
                type="button"
                onClick={openImportModal}
                disabled={isSRUser() && !isAuthorizedToDR}
              >
                Upload Module Data
              </Button>
            </Grid>
          )}
        </Grid>
        {isDraftDataLoading && isSubmittedDataLoading ? (
          <div className="pp-dashboard-spinner-container">
            <div className="pp-dashboard-spinner">
              <Spinner />
            </div>
          </div>
        ) : (
          <>
            {isAdmin() && !isJOUser() && (
              <Grid row className="what-are-submission-status">
                <Grid col={12}>
                  <Button
                    type="button"
                    unstyled
                    id="openModuleSubmissionStatuses"
                    className="submission-status-unstyled-button"
                    onClick={openSubmissionStatusModal}
                  >
                    <p>What are module submission statuses?</p>
                  </Button>
                </Grid>
              </Grid>
            )}
            <Grid>
              {/*  Render tabs only for admin users in DR/SR organizations*/}
              {isAdmin() && !isJOUser() ? (
                <Tabs value={currentTab}>
                  <TabsList onClick={setTabValue} id="moduleDataTabsList">
                    <Tab id="all" value="all">
                      All ({noPendingApproval + noSubmitted + noRejected + noDrafts + noError})
                    </Tab>
                    {(isSRUser() || isDRUser()) && (
                      <Tab id="drafts" value="drafts">
                        Drafts ({noDrafts})
                      </Tab>
                    )}
                    {(isSRUser() || isDRUser()) && (
                      <Tab id="pending-approval" value="pending-approval">
                        Pending Approval ({noPendingApproval})
                      </Tab>
                    )}
                    {(isSRUser() || isDRUser()) && (
                      <Tab id="submitted" value="submitted">
                        {isSRUser() ? "Approved" : "Submitted"} ({noSubmitted})
                      </Tab>
                    )}
                    {(isSRUser() || isDRUser()) && (
                      <Tab id="rejected" value="rejected">
                        Rejected ({noRejected})
                      </Tab>
                    )}
                    {(isSRUser() || isDRUser()) && (
                      <Tab id="errors" value="errors">
                        Errors ({noError})
                      </Tab>
                    )}
                    <div></div>
                  </TabsList>
                  <div>
                    <TabPanel value="all">
                      {isSRUser() && !isAuthorizedToDR ? (
                        <>{summaryDetailsBox()}</>
                      ) : (
                        <SubmittalsTabTable
                          setColumnDefinitionsModal={openColumnDefinitionsModal}
                          setErrorGuidanceModal={openErrorGuidanceModal}
                          setErrorDownloadModal={openErrorDownloadModal}
                          setImportModal={openImportModal}
                          setCurrUploadId={getCurrentUploadId}
                          setCurrModuleName={getCurrentModuleName}
                          setCSVModal={openCSVDownloadModal}
                          setRemoveModalData={handleAction}
                          tab={"all"}
                          draftsData={drafts}
                          pendingApprovalData={pendingApproval}
                          submittedData={submitted}
                          rejectedData={rejected}
                          errorsData={isJOUser() ? [] : error}
                          isSubmittedDataLoading={isSubmittedDataLoading}
                        />
                      )}
                    </TabPanel>
                    {(isSRUser() || isDRUser()) && (
                      <TabPanel value="drafts">
                        {!isAuthorizedToDR ? (
                          summaryDetailsBox()
                        ) : (
                          <DraftsTabTable
                            setImportModal={openImportModal}
                            setColumnDefinitionsModal={openColumnDefinitionsModal}
                            setCurrUploadId={getCurrentUploadId}
                            setCSVModal={openCSVDownloadModal}
                            draftsData={drafts}
                          />
                        )}
                      </TabPanel>
                    )}
                    {(isSRUser() || isDRUser()) && (
                      <TabPanel value="pending-approval">
                        {!isAuthorizedToDR ? (
                          summaryDetailsBox()
                        ) : (
                          <SubmittalsTabTable
                            setColumnDefinitionsModal={openColumnDefinitionsModal}
                            setImportModal={openImportModal}
                            setCurrUploadId={getCurrentUploadId}
                            setCSVModal={openCSVDownloadModal}
                            tab={"pending-approval"}
                            pendingApprovalData={pendingApproval}
                            isSubmittedDataLoading={isSubmittedDataLoading}
                          />
                        )}
                      </TabPanel>
                    )}
                    {(isSRUser() || isDRUser()) && (
                      <TabPanel value="submitted">
                        {!isAuthorizedToDR ? (
                          summaryDetailsBox()
                        ) : (
                          <SubmittalsTabTable
                            setColumnDefinitionsModal={openColumnDefinitionsModal}
                            setImportModal={openImportModal}
                            setCurrUploadId={getCurrentUploadId}
                            setCSVModal={openCSVDownloadModal}
                            tab={"submitted"}
                            submittedData={submitted}
                            isSubmittedDataLoading={isSubmittedDataLoading}
                          />
                        )}
                      </TabPanel>
                    )}
                    {(isSRUser() || isDRUser()) && (
                      <TabPanel value="rejected">
                        {!isAuthorizedToDR ? (
                          summaryDetailsBox()
                        ) : (
                          <SubmittalsTabTable
                            setColumnDefinitionsModal={openColumnDefinitionsModal}
                            setImportModal={openImportModal}
                            setCurrUploadId={getCurrentUploadId}
                            setCSVModal={openCSVDownloadModal}
                            setRemoveModalData={handleAction}
                            tab={"rejected"}
                            rejectedData={rejected}
                            isSubmittedDataLoading={isSubmittedDataLoading}
                          />
                        )}
                      </TabPanel>
                    )}
                    {(isSRUser() || isDRUser()) && (
                      <TabPanel value="errors">
                        {!isAuthorizedToDR ? (
                          summaryDetailsBox()
                        ) : (
                          <SubmittalsTabTable
                            setColumnDefinitionsModal={openColumnDefinitionsModal}
                            setErrorGuidanceModal={openErrorGuidanceModal}
                            setErrorDownloadModal={openErrorDownloadModal}
                            setImportModal={openImportModal}
                            setCurrUploadId={getCurrentUploadId}
                            setCurrModuleName={getCurrentModuleName}
                            setCSVModal={openCSVDownloadModal}
                            setRemoveModalData={handleAction}
                            tab={"errors"}
                            errorsData={error}
                            isSubmittedDataLoading={isSubmittedDataLoading}
                          />
                        )}
                      </TabPanel>
                    )}
                  </div>
                </Tabs>
              ) : (
                <SubmittalsTabTable
                  setColumnDefinitionsModal={openColumnDefinitionsModal}
                  setImportModal={openImportModal}
                  setCurrUploadId={getCurrentUploadId}
                  setCSVModal={openCSVDownloadModal}
                  tab={"submitted"}
                  submittedData={submitted}
                  isSubmittedDataLoading={isSubmittedDataLoading}
                />
              )}
            </Grid>
          </>
        )}
        {isImportModalOpen && <ImportModal onClose={closeImportModal} />}
        {isColumnDefinitionsModalOpen && (
          <ColumnDefinitionsModal table_name={colDefModalValue} onClose={closeColumnDefinitionsModal} />
        )}
        {isErrorGuidanceModalOpen && <ErrorGuidanceModal onClose={closeErrorGuidanceModal} />}
        {isCSVDownloadModalOpen && (
          <CSVDownloadModal apiPath="data" uploadId={currUploadId} onClose={closeCSVDownloadModal} />
        )}
        {isErrorDownloadModalOpen && (
          <CSVDownloadModal
            apiPath="import-error-data"
            uploadId={currUploadId}
            moduleName={currModuleName}
            onClose={closeErrorDownloadModal}
          />
        )}
        {isSubmissionStatusModalOpen && <SubmissionStatusModal onClose={closeSubmissionStatusModal} />}
        {isRemoveConfirmationModalOpen && (
          <RemoveConfirmationModal
            onClose={closeRemoveModuleModal}
            moduleName={selectedRemoveModule.module_name}
            year={selectedRemoveModule.year}
            subRecipient={null}
            moduleType={selectedRemoveModule.module_frequency}
            moduleStatus={selectedRemoveModule.submission_status}
            updatedBy={selectedRemoveModule.updated_by}
            uploadId={selectedRemoveModule.upload_id}
          />
        )}
      </GridContainer>
    </div>
  );
}

export default ModuleData;
