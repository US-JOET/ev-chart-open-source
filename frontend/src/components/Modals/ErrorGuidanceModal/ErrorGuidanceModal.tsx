/**
 * Modal for guidance on errors from module upload.
 * @packageDocumentation
 **/
import React from "react";

import { Button, Modal, ModalHeading, ModalFooter } from "evchartstorybook";

import errorGuidanceGraphic from "../../../assets/ErrorGuidanceGraphic.png";

import "./ErrorGuidanceModal.css";
import "../Modal.css";

/**
 * Interface defining the props that are passed to the ErrorGuidanceModal component
 */
interface ErrorGuidanceModalProps {
  onClose: () => void;
}

/**
 * ErrorGuidanceModal
 * @param ErrorGuidanceModalProps
 * @returns the error guidance modal
 */
export const ErrorGuidanceModal: React.FC<ErrorGuidanceModalProps> = ({ onClose }): React.ReactElement => {
  return (
    <div className="error-guidance-modal">
      <Modal onClose={onClose}>
        <ModalHeading id="modal-2-heading" className="bottom-border">
          How do I read an error report?
        </ModalHeading>
        <div className="modal-body">
          <div className="modal-text">
            Using the column, the row, and the error description, correct your CSV file and reupload a new data
            submission.{" "}
            <div className="error-guidance-container">
              <img
                id="errorGuidanceGraphic"
                className="error-guidance-graphic"
                src={errorGuidanceGraphic}
                alt="Error Guidance Graphic"
                title="Error Guidance Graphic"
              />
              <p>
                <b>Example:</b> using columns <b>A, B, and C</b> you will be able to pinpoint the error that has occured
                with your upload.
              </p>
            </div>
          </div>
        </div>
        <ModalFooter>
          <Button onClick={onClose} type="button">
            Close
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
};

export default ErrorGuidanceModal;
