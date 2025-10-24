/**
 * Cancel modal used throughout the application.
 * @packageDocumentation
 **/
import React from "react";
import { useNavigate } from "react-router";

import { Button, ButtonGroup, Modal, ModalHeading, ModalFooter } from "evchartstorybook";

import "../Modal.css";

/**
 * Interface defining the props for the CancelModal
 */
interface CancelModalProps {
  navigateUrl: string;
  onClose: () => void;
}

/**
 *
 * @param CancelModalProps the props passed to the modal
 * @returns
 */
export const CancelModal: React.FC<CancelModalProps> = ({ navigateUrl, onClose }): React.ReactElement => {
  /**
   * Method for changing the location / route
   */
  const navigate = useNavigate();

  return (
    <div className="cancel-modal">
      <Modal onClose={onClose} aria-labelledby="modal-1-heading" aria-describedby="modal-1-description">
        <ModalHeading id="modal-2-heading">Confirm Cancellation</ModalHeading>
        <div className="modal-body">
          <div className="modal-subheader">Are you sure you want to cancel?</div>
          <div className="modal-text">All of your progress will be lost. You cannot undo this action.</div>
        </div>
        <ModalFooter>
          <ButtonGroup>
            <Button
              onClick={() => {
                navigate(navigateUrl);
              }}
              type="button"
            >
              Cancel
            </Button>
            <Button onClick={onClose} type="button" unstyled className="padding-105 text-center">
              Go Back
            </Button>
          </ButtonGroup>
        </ModalFooter>
      </Modal>
    </div>
  );
};

export default CancelModal;
