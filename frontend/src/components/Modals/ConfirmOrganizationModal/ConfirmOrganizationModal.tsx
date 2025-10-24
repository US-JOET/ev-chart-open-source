/**
 * Modal for confirming addition of an organization.
 * @packageDocumentation
 **/
import React, { useEffect, useState } from "react";

import { FocusTrap } from "@mui/base/FocusTrap";

import { Alert, Button, ButtonGroup, Checkbox, Modal, ModalHeading, ModalFooter, Spinner } from "evchartstorybook";

import { NewOrgInfo } from "../../../interfaces/Organization/organizations-interface";

import { isJOUser } from "../../../utils/authFunctions";
import { PATH_ORG } from "../../../utils/pathConstants";

import "./ConfirmOrganizationModal.css";
import "../Modal.css";

/**
 * Interface defining the props that are passed to the ConfirmationOrganizationModalProps component
 */
interface ConfirmationOrganizationModalProps {
  orgName: string;
  firstName: string;
  lastName: string;
  email: string;
  orgType: string | null;
  success: () => void;
  invalidUser: () => void;
  onClose: () => void;
}

/**
 *
 * @param ConfirmationOrganizationModalProps
 * @returns the confirm organization modal
 */
export const ConfirmOrganizationModal: React.FC<ConfirmationOrganizationModalProps> = ({
  orgName,
  firstName,
  lastName,
  email,
  orgType,
  onClose,
  success,
  invalidUser,
}): React.ReactElement => {
  /**
   * Get id token for endpoint authorization
   */
  const access_token = localStorage.getItem("access_token");

  /**
   * Get the api url from the environment variables
   */
  const API_URL = import.meta.env.VITE_API_URL;

  /**
   * State variables for modal
   */
  const [showSpinner, setShowSpinner] = useState(false);
  const [confirmChecked, setConfirmChecked] = useState(true);
  const [orgInfo, setOrgInfo] = useState<NewOrgInfo>({
    org_name: orgName,
    first_name: firstName,
    last_name: lastName,
    email: email,
  });

  /**
   * Handle confirming checkbox
   */
  const handleCheckboxChange = () => {
    setConfirmChecked((prevChecked) => !prevChecked);
  };

  /**
   * Set the org type being created for JO users (DR/SR)
   */
  useEffect(() => {
    if (orgType) {
      setOrgInfo((prevState) => ({ ...prevState, org_type: orgType }));
    }
  }, []);

  /**
   * Event tied to handle submit
   */
  const handleSubmit = () => {
    setShowSpinner(true);
    fetch(`${API_URL}${PATH_ORG}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `${access_token}`,
      },
      body: JSON.stringify(orgInfo),
    })
      .then((response) => {
        if (response.ok) {
          return response.json();
        } else {
          throw response;
        }
      })
      .then(() => {
        success();
      })
      .catch((err) => {
        const errorCode = err.status;
        //error case: invalid email (already in use)
        console.log(errorCode);
        invalidUser();
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
              <ModalHeading id="confirmOrganizationModalHeading" className="bottom-border">
                Review and Confirm Organization Information
              </ModalHeading>
              <Alert slim type="warning" headingLevel="h3" className="organization-confirm-alert">
                Organization name and administrator user information may not be edited once added to EV-ChART.
              </Alert>
              <h3 className="org-info-sub-heading">Organization Information</h3>
              <div className="confirm-organization-modal-field">
                <p className="confirm-organization-modal-label">New Organization Name:</p>
                <p className="confirm-organization-modal-data">{orgName}</p>
              </div>
              {isJOUser() && (
                <div className="confirm-organization-modal-field">
                  <p className="confirm-organization-modal-label">New Organization Type:</p>
                  <p className="confirm-organization-modal-data">
                    {orgType === "direct-recipient" ? "Direct Recipient" : "Subrecipient/ Contractor"}
                  </p>
                </div>
              )}
              <div className="confirm-organization-modal-field">
                <p className="confirm-organization-modal-label">New Administrator Name:</p>
                <p className="confirm-organization-modal-data">{firstName + " " + lastName}</p>
              </div>
              <div className="confirm-organization-modal-field">
                <p className="confirm-organization-modal-label">New Administrator Email:</p>
                <p className="confirm-organization-modal-data">{email}</p>
              </div>

              <div className="checkbox add-org-checkbox">
                <Checkbox
                  id="addOrgCheckbox"
                  name="checkbox"
                  label={`I confirm that I verified the organization name and administrator information with the ${orgType === "direct-recipient" ? "direct recipient" : "subrecipient/contractor"} I am adding to EV-ChART.`}
                  onChange={handleCheckboxChange}
                />
              </div>
              <ModalFooter>
                <ButtonGroup className="modal-button-group">
                  <Button type="button" disabled={confirmChecked} onClick={handleSubmit}>
                    Confirm & Add Organization
                  </Button>
                  <Button type="button" unstyled className="padding-105 text-center" onClick={onClose}>
                    Cancel
                  </Button>
                </ButtonGroup>
              </ModalFooter>
            </>
          )}
        </Modal>
      </div>
    </FocusTrap>
  );
};

export default ConfirmOrganizationModal;
