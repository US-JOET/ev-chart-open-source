/**
 * Modal to submit a module.
 * @packageDocumentation
 **/
import React, { useState, useEffect, ReactNode } from "react";
import { useNavigate } from "react-router-dom";

import { FocusTrap } from "@mui/base/FocusTrap";

import { Alert, Button, ButtonGroup, Checkbox, Modal, ModalHeading, ModalFooter, Spinner } from "evchartstorybook";

import { isSRUser } from "../../../utils/authFunctions";
import { getName, getOrgID, getScope } from "../../../utils/getJWTInfo";
import { FeatureFlagEnum, getFeatureFlagValue, getFeatureFlagList } from "../../../utils/FeatureToggle";
import { PATH_MODULE_SUBMIT, PATH_SUBMITTING_NULL } from "../../../utils/pathConstants";
import { ROUTE_MODULE_DATA } from "../../../utils/routeConstants";

import "./SubmissionModal.css";
import "../Modal.css";

/**
 * Interface defining the props for the SubmitModuleModalProps
 */
interface SubmitModuleModalProps {
  moduleName: string;
  year: string;
  directRecipient: string;
  moduleType: string;
  uploadId: string;
  onClose: () => void;
}

/**
 * SubmitModuleModal
 * @param SubmitModuleModalProps
 * @returns the submit module modal
 */
export const SubmitModuleModal: React.FC<SubmitModuleModalProps> = ({
  moduleName,
  year,
  directRecipient,
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
   * Get org info from jwt
   */
  const jwtOrgID = getOrgID();
  const recipientType = getScope();

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
  const [showSpinner, setShowSpinner] = useState(false);
  const [confirmChecked, setConfirmChecked] = useState(true);
  const [submitClicked, setSubmitClicked] = useState(false);
  const [confirmationStatement, setConfirmationStatement] = useState("");
  const [submissionInfo, setSubmissionInfo] = useState(true);

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
      } else if (module_id === "5") {
        setNullModalHeading("Confirm No Maintenance Costs");
      } else if (module_id === "9") {
        setNullModalHeading("No Capital & Installation Costs");
      }
    }
  }, [moduleFiveNullFeatureFlag, bizMagicFeatureFlag]);

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
            Confirm below that for the data records left blank, there were no charging sessions in the <b>{year} </b>
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
            setSubmissionInfo(true);
          }
        })
        .catch((err) => {
          console.log(err);
        })
        .finally(() => {
          setShowSpinner(false);
        });
    }
  }, [moduleFiveNullFeatureFlag, bizMagicFeatureFlag]);

  /**
   * Set the relevant confirmation statement
   */
  useEffect(() => {
    if (recipientType === "direct-recipient") {
      setConfirmationStatement(
        "I confirm that I am authorized to submit this data and that this data is accurate to the best of my knowledge.",
      );
    } else {
      setConfirmationStatement(
        "I confirm that I am authorized to upload this data on behalf of the " +
          directRecipient +
          " and that this data is accurate to the best of my knowledge.",
      );
    }
  }, []);

  /**
   * Event tied to confirm checkbox
   */
  const handleCheckboxChange = () => {
    setConfirmChecked((prevChecked) => !prevChecked);
  };

  /**
   * Event tied to confirm nulls checkbox
   */
  const handleConfirmedCheckboxChange = () => {
    setConfirmedNullChecked((prevChecked) => !prevChecked);
  };

  /**
   * Event tied to submit nulls button
   */
  const clickConfirmNulls = () => {
    setClickedSubmitNulls(true);
    handleSubmitData();
  };

  /**
   * Handle submitting module
   */
  const handleSubmit = () => {
    setSubmitClicked(true);
    if (submittingNulls) {
      setSubmissionInfo(false);
      setRenderConfirmNulls(true);
    } else {
      handleSubmitData();
    }
  };

  /**
   * Post data through the API
   */
  const handleSubmitData = () => {
    setShowSpinner(true);
    const submitterName = getName();

    const submitData = {
      upload_id: uploadId,
      submitted_by: submitterName,
      org_id: jwtOrgID,
      recipient_type: recipientType,
    };

    fetch(`${API_URL}${PATH_MODULE_SUBMIT}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `${access_token}`,
      },
      body: JSON.stringify(submitData),
    })
      .then((response) => {
        if (response.ok) {
          return response.json();
        } else {
          throw response;
        }
      })
      .then(() => {
        onClose();
        // Allow the parent page to be refreshed always on submission of draft
        localStorage.removeItem("beenRefreshed");
        // Navigate to the tabs page with the state info
        navigate(ROUTE_MODULE_DATA, {
          state: {
            startTab: isSRUser() ? "pending-approval" : "submitted",
            showSubmitSuccessModal: true,
            showConflictModal: false,
            moduleName: moduleName,
            moduleYear: year,
            moduleType: moduleType,
            directRecipient: directRecipient,
            forceRefresh: true,
          },
        });
      })
      .catch((err) => {
        const errorCode = Number(err.status);
        if (errorCode === 409) {
          localStorage.removeItem("beenRefreshed");
          onClose();
          navigate(ROUTE_MODULE_DATA, {
            state: {
              startTab: "errors",
              showSubmitSuccessModal: false,
              showConflictModal: true,
              moduleName: moduleName,
              moduleYear: year,
              moduleType: moduleType,
              directRecipient: directRecipient,
              forceRefresh: true,
            },
          });
        }
      });
  };

  return (
    <FocusTrap open>
      <div tabIndex={-1}>
        <Modal onClose={onClose}>
          {showSpinner ? (
            <>
              <div className="spinner-modal-body">
                <Spinner></Spinner>
              </div>
            </>
          ) : (
            <>
              {submissionInfo && (
                <>
                  <ModalHeading id="submitModalHeading" className="bottom-border">
                    Submit Module Data
                  </ModalHeading>
                  <h2>{moduleName}</h2>
                  <div className="submission-modal-field">
                    <p className="submission-modal-label">Reporting Year:</p>
                    <p>{year}</p>
                  </div>
                  <div className="submission-modal-field">
                    <p className="submission-modal-label">Direct Recipient:</p>
                    <p>{directRecipient}</p>
                  </div>
                  <div className="submission-modal-field">
                    <p className="submission-modal-label">Type:</p>
                    <p>{moduleType}</p>
                  </div>
                  <div className="submission-modal-field">
                    <p className="submission-modal-label">Upload ID:</p>
                    <p>{uploadId}</p>
                  </div>
                  <div className="checkbox">
                    <Checkbox
                      id="submitModuleCheckbox"
                      name="checkbox"
                      label={confirmationStatement}
                      onChange={handleCheckboxChange}
                    />
                  </div>
                  <ModalFooter>
                    <ButtonGroup className="modal-button-group">
                      <Button type="button" disabled={confirmChecked || submitClicked} onClick={handleSubmit}>
                        Submit
                      </Button>
                      <Button type="button" unstyled className="padding-105 text-center" onClick={onClose}>
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
    </FocusTrap>
  );
};

export default SubmitModuleModal;
