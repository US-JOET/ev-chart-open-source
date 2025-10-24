/**
 * Approve Module Modal.
 * @packageDocumentation
 **/
import React, { ReactNode, useEffect, useState } from "react";
import { useNavigate } from "react-router";

import {
  Button,
  ButtonGroup,
  ErrorMessage,
  Grid,
  Modal,
  ModalHeading,
  ModalFooter,
  Textarea,
  Spinner,
  Checkbox,
  Alert,
} from "evchartstorybook";

import { FeatureFlagEnum, getFeatureFlagValue, getFeatureFlagList } from "../../../utils/FeatureToggle";
import { PATH_MODULE_SUBMISSION_APPROVAL, PATH_SUBMITTING_NULL } from "../../../utils/pathConstants";
import { ROUTE_MODULE_DATA } from "../../../utils/routeConstants";

import "./ApproveModal.css";
import "../Modal.css";

/**
 * Interface defining the props that are passed to the ApproveModal component
 */
interface ApproveModalProps {
  moduleName: string;
  year: string;
  subrecipient: string;
  directRecipient: string;
  updatedOn: string;
  updatedBy: string;
  moduleType: string;
  uploadId: string;
  onClose: () => void;
}

/**
 * ApproveModal
 * @param ApproveModalProps information about the module being approved
 * @returns the approval modal
 */
export const ApproveModal: React.FC<ApproveModalProps> = ({
  moduleName,
  year,
  subrecipient,
  directRecipient,
  updatedOn,
  updatedBy,
  moduleType,
  uploadId,
  onClose,
}): React.ReactElement => {
  /**
   * Method for changing the location / route
   */
  const navigate = useNavigate();

  /**
   * Get the api url from the environment variables
   */
  const API_URL = import.meta.env.VITE_API_URL;

  /**
   * Get access token for endpoint authorization
   */
  const access_token = localStorage.getItem("access_token");

  /**
   * Parse from the module name which module (2-9) is being approved
   */
  const module_id = moduleName.substring(7, 8);

  /**
   * Feature flag management
   */
  const [bizMagicFeatureFlag, setBizMagicFeatureFlag] = useState(false);
  const [moduleFiveNullFeatureFlag, setModuleFiveNullFeatureFlag] = useState(false);
  useEffect(() => {
    getFeatureFlagList().then((results) => {
      setBizMagicFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.BizMagic));
      setModuleFiveNullFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.ModuleFiveNulls));
    });
  }, []);

  /**
   * State variables
   */
  const [approvalComments, setApprovalComments] = useState<string>("");
  const [remainingChars, setRemainingChars] = useState<number>(200);
  const [APIError, setAPIError] = useState(false);
  const [showSpinner, setShowSpinner] = useState(false);
  const [submitClicked, setSubmitClicked] = useState(false);
  const [approvalInfo, setApprovalInfo] = useState(true);

  /**
   * Confirm nulls state variables
   */
  const [confirmNullChecked, setConfirmedNullChecked] = useState(true);
  const [submittingNulls, setSubmittingNulls] = useState(false);
  const [renderConfirmNulls, setRenderConfirmNulls] = useState(false);
  const [clickedSubmitNulls, setClickedSubmitNulls] = useState(false);
  const [nullModalHeading, setNullModalHeading] = useState("");
  const [nullModalDescription, setNullModalDescription] = useState<string | ReactNode>("");
  const [nullModalConfirmation, setNullModalConfirmation] = useState("");

  /**
   * useEffect for setting confirm nulls headings
   */
  useEffect(() => {
    if (
      (moduleFiveNullFeatureFlag && module_id === "5") ||
      bizMagicFeatureFlag
    ) {
      if (module_id === "2") {
        setNullModalHeading("Confirm No Charging Sessions");
      } else if (module_id === "3") {
        setNullModalHeading("Confirm No Uptime");
      } else if (module_id === "4") {
        setNullModalHeading("Confirm No Outages");
      } else if (module_id === "5") setNullModalHeading("Confirm No Maintenance Costs");
    } else if (module_id === "9") {
      setNullModalHeading("No Capital & Installation Costs");
    }
  }, [moduleFiveNullFeatureFlag, bizMagicFeatureFlag]);

  /**
   * Set spinner while null acknowledgment checks are running
   */
  useEffect(() => {
    const timer = setTimeout(() => {
      setShowSpinner(false);
    }, 2000);
    return () => clearTimeout(timer);
  }, []);

  /**
   * Checks for null records for appropriate modules
   */
  useEffect(() => {
    if (
      (moduleFiveNullFeatureFlag && module_id === "5") ||
      bizMagicFeatureFlag
    ) {
      if (module_id === "2") {
        setNullModalDescription(
          <>
            Confirm below that for the data records left blank, there were no charging sessions in the{" "}
            <b>{moduleType}</b> reporting period.
          </>,
        );
      } else if (module_id === "3") {
        setNullModalDescription(
          <>
            Confirm below that for <b>Module 3 Uptime values</b> left blank, the associated{" "}
            <b>ports have been operational for less than one (1) year</b> in the <b>{moduleType}</b> reporting period.
          </>,
        );
      } else if (module_id === "4") {
        setNullModalDescription(
          <>
            Confirm below that for <b>Module 4</b> records left blank, there were <b>no outages</b> in the{" "}
            <b>{moduleType}</b> reporting period.
          </>,
        );
      } else if (module_id === "5") {
        setNullModalDescription(
          <>
            Confirm below that for <b>Module 5</b> records left blank, there were <b>no maintenance costs</b> in the{" "}
            <b>
              {year} {moduleType}
            </b>{" "}
            reporting period.
          </>,
        );
      } else if (module_id === "9") {
        setNullModalDescription(
          <>
            Confirm below that for <b>Module 9</b> records left blank, there were{" "}
            <b>no capital & installation costs.</b>
          </>,
        );
      }
    }
  }, [moduleFiveNullFeatureFlag, bizMagicFeatureFlag]);

  /**
   * useEffect for setting confirm nulls confirmation
   */
  useEffect(() => {
    if (
      (moduleFiveNullFeatureFlag && module_id === "5") ||
      bizMagicFeatureFlag
    ) {
      if (module_id === "2") {
        setNullModalConfirmation(
          "I confirm that there were no applicable charging sessions for the records and data attributes that I have left blank.",
        );
      } else if (module_id === "3") {
        setNullModalConfirmation(
          "I confirm that the ports have been operational for less that a year for the uptime values that I have left blank.",
        );
      } else if (module_id === "4") {
        setNullModalConfirmation(
          "I confirm that there were no applicable outages for the records and data attributes that I have left blank.",
        );
      } else if (module_id === "5") {
        setNullModalConfirmation(
          "I confirm that there were no applicable maintenance costs for the records and data attributes that I have left blank.",
        );
      } else if (module_id === "9") {
        setNullModalConfirmation(
          "I confirm that there were no applicable capital & installation costs for the records and data attributes that I have left blank.",
        );
      }
    }
  }, [moduleFiveNullFeatureFlag, bizMagicFeatureFlag]);

  /**
   * useEffect for checking if nulls are being submitted
   */
  useEffect(() => {
    if (
      (moduleFiveNullFeatureFlag && module_id === "5") ||
      bizMagicFeatureFlag
    ) {
      setShowSpinner(true);
      fetch(`${API_URL}${PATH_SUBMITTING_NULL}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `${access_token}`,
          upload_id: uploadId,
          module_id: moduleName.substring(7, 8),
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
          if (data === true) {
            setSubmittingNulls(true);
          } else if (data === false) {
            setApprovalInfo(true);
          }
        })
        .catch((err) => {
          console.log(err);
        })
        .finally(() => setShowSpinner(false));
      setShowSpinner(false);
    }
  }, [moduleFiveNullFeatureFlag, bizMagicFeatureFlag]);

  /**
   * Event tied to module approval being clicked
   */
  const approveModule = () => {
    const submitData = {
      upload_id: uploadId,
      submission_status: "Approved",
      comments: approvalComments,
    };

    fetch(`${API_URL}${PATH_MODULE_SUBMISSION_APPROVAL}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `${access_token}`,
      },
      body: JSON.stringify(submitData),
    })
      .then(() => {
        // Allow the parent page to be refreshed always on submission of draft
        localStorage.removeItem("beenRefreshed");
        // Navigate to the tabs page with the state info
        navigate(ROUTE_MODULE_DATA, {
          state: {
            startTab: "submitted",
            showApprovedSuccessModal: true,
            moduleName: moduleName,
            moduleYear: year,
            moduleType: moduleType,
            directRecipient: directRecipient,
            forceRefresh: true,
          },
        });
      })
      .catch((err) => {
        console.log(err.message);
        setAPIError(true);
      });
  };

  /**
   * Event tied to typing comments
   * @param comments the comments being typed
   */
  const updateApprovalField = (comments: string) => {
    setApprovalComments(comments);
    setRemainingChars(200 - comments.length);
  };

  /**
   * Event tied to confirm nulls checkbox
   */
  const handleConfirmedCheckboxChange = () => {
    setConfirmedNullChecked((prevChecked) => !prevChecked);
  };

  /**
   * Event tied to submit nulls
   */
  const clickConfirmNulls = () => {
    setClickedSubmitNulls(true);
    approveModule();
  };

  /**
   * Event tied to user clicking initial submit
   */
  const handleSubmit = () => {
    setSubmitClicked(true);
    if (submittingNulls) {
      setApprovalInfo(false);
      setRenderConfirmNulls(true);
    } else {
      approveModule();
    }
  };

  return (
    <div className="approve-modal">
      <Modal onClose={onClose} aria-labelledby="modal-1-heading" aria-describedby="modal-1-description">
        {showSpinner ? (
          <div className="spinner-modal-body">
            <Spinner></Spinner>
          </div>
        ) : (
          <>
            {approvalInfo && (
              <>
                <ModalHeading id="approveModalHeading" className="bottom-border">
                  Approve
                </ModalHeading>
                <div className="modal-body">
                  <div className="modal-subheader">{moduleName}</div>
                  <Grid row className="approve-modal-field">
                    <Grid col={6} className="approve-modal-label">
                      Reporting Year:
                    </Grid>
                    <Grid col={6} className="approve-modal-value">
                      {year}
                    </Grid>
                  </Grid>
                  <Grid row className="approve-modal-field">
                    <Grid col={6} className="approve-modal-label">
                      Type:
                    </Grid>
                    <Grid col={6} className="approve-modal-value">
                      {moduleType}
                    </Grid>
                  </Grid>
                  <Grid row className="approve-modal-field">
                    <Grid col={6} className="approve-modal-label">
                      Subrecipient/Contractor:
                    </Grid>
                    <Grid col={6} className="approve-modal-value">
                      {subrecipient}
                    </Grid>
                  </Grid>
                  <Grid row className="approve-modal-field">
                    <Grid col={6} className="approve-modal-label">
                      Updated On:
                    </Grid>
                    <Grid col={6} className="approve-modal-value">
                      {updatedOn}
                    </Grid>
                  </Grid>
                  <Grid row className="approve-modal-field">
                    <Grid col={6} className="approve-modal-label">
                      Updated By:
                    </Grid>
                    <Grid col={6} className="approve-modal-value">
                      {updatedBy}
                    </Grid>
                  </Grid>
                  <Grid row className="approve-modal-field">
                    <Grid col={6} className="approve-modal-label">
                      Upload ID:
                    </Grid>
                    <Grid col={6} className="approve-modal-value">
                      {uploadId}
                    </Grid>
                  </Grid>
                  <div className="approval-modal-comments">
                    <p className="approve-comments-label">Feedback from Reviewer</p>
                    <Textarea
                      id="approvalComments"
                      name="approval-comments"
                      maxLength={200}
                      onChange={(e) => {
                        updateApprovalField(e.target.value);
                      }}
                    />
                    <p className="approval-comments-counter">Characters Remaining: {remainingChars}/200</p>
                  </div>
                </div>
                {APIError && <ErrorMessage> An error has occurred. Please try again. </ErrorMessage>}
                <ModalFooter id="approveModalFooter">
                  <ButtonGroup>
                    <Button disabled={submitClicked} onClick={handleSubmit} type="button">
                      Approve
                    </Button>
                    <Button onClick={onClose} type="button" unstyled className="padding-105 text-center">
                      Cancel
                    </Button>
                  </ButtonGroup>
                </ModalFooter>
              </>
            )}
            {renderConfirmNulls && (
              <>
                <ModalHeading id="zeroAckHeading" className="bottom-border">
                  {nullModalHeading}
                </ModalHeading>
                <Alert type="warning" headingLevel="h3" className="submission-alert">
                  Do not submit this data until all applicable data for this submission has been collected.
                </Alert>
                <div className="null-field-text">{nullModalDescription}</div>
                <div className="checkbox">
                  <Checkbox
                    id="submitModuleCheckbox"
                    name="checkbox"
                    label={nullModalConfirmation}
                    onChange={handleConfirmedCheckboxChange}
                  />
                </div>
                <ModalFooter>
                  <ButtonGroup className="modal-button-group">
                    <Button
                      type="button"
                      disabled={confirmNullChecked || clickedSubmitNulls}
                      onClick={clickConfirmNulls}
                    >
                      Confirm and Submit
                    </Button>
                    <Button type="button" unstyled className="padding-105 text-center" onClick={onClose}>
                      Cancel
                    </Button>
                  </ButtonGroup>
                </ModalFooter>
              </>
            )}
          </>
        )}
      </Modal>
    </div>
  );
};

export default ApproveModal;
