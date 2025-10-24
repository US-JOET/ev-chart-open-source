/**
 * Terms and condition modal shown on user login.
 * @packageDocumentation
 **/
import React, { useState } from "react";

import { Button, ButtonGroup, Checkbox, Modal, ModalHeading, ModalFooter } from "evchartstorybook";

import { TermsAndConditions } from "./EVChartTermsAndConditions";

import "./TermsAndConditionsModal.css";
import "../Modal.css";

/**
 * Interface defining the props that are passed to the RejectModal component
 */
interface TermsAndConditionsModalProps {
  onClose: () => void;
}

/**
 * TermsAndConditionsModal
 * @param TermsAndConditionsModalProps
 * @returns the terms and conditions modal
 */
export const TermsAndConditionsModal: React.FC<TermsAndConditionsModalProps> = ({ onClose }): React.ReactElement => {
  /**
   * Get the api url and environment variables
   */
  const API_URL = import.meta.env.VITE_API_URL;
  const hostname = import.meta.env.VITE_HOSTNAME;
  const clientId = import.meta.env.VITE_CLIENTID;
  const region = import.meta.env.VITE_REGION;

  /**
   * state variable for managing if confirm has been selected
   */
  const [confirmChecked, setConfirmChecked] = useState(true);

  /**
   * Event tied to user confirming checkbox
   */
  const handleCheckboxChange = () => {
    setConfirmChecked((prevChecked) => !prevChecked);
  };

  /**
   * Event tied to the signout
   */
  const signOut = () => {
    localStorage.clear();
    window.location.href = `https://${hostname}.auth-fips.${region}.amazoncognito.com/logout?client_id=${clientId}&logout_uri=${API_URL}`;
  };

  /**
   * accept conditions functions
   */
  const acceptConditions = () => {
    localStorage.setItem("termsAccepted", "true");
    onClose();
  };

  return (
    <div className="terms-and-conditions-modal">
      <Modal
        onClose={signOut}
        forceAction={true}
        aria-labelledby="terms-and-conditions-heading"
        aria-describedby="terms-and-conditions-description"
      >
        <ModalHeading id="terms-and-conditions-heading">EV-ChART Terms of Use</ModalHeading>
        <div className="modal-body">
          <div className="modal-text terms-and-conditions-content">{TermsAndConditions}</div>
        </div>
        <div className="checkbox">
          <Checkbox
            id="submitModuleCheckbox"
            name="checkbox"
            label={"I have read and agree to the EV-ChART Terms of Use."}
            onChange={handleCheckboxChange}
          />
        </div>
        <ModalFooter>
          <ButtonGroup>
            <Button onClick={acceptConditions} type="button" disabled={confirmChecked}>
              Accept
            </Button>
            <Button onClick={signOut} type="button" unstyled className="padding-105 text-center">
              Close
            </Button>
          </ButtonGroup>
        </ModalFooter>
      </Modal>
    </div>
  );
};

export default TermsAndConditionsModal;
