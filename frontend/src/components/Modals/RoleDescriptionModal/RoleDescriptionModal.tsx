/**
 * Modal for Role Description from add user.
 * @packageDocumentation
 **/
import React from "react";

import { Button, Modal, ModalHeading, ModalFooter } from "evchartstorybook";

import roleDescriptionGraphic from "../../../assets/RoleDescriptionsGraphic.png";

import "../Modal.css";

interface RoleDescriptionModalProps {
  onClose: () => void;
}

export const RoleDescriptionModal: React.FC<RoleDescriptionModalProps> = ({ onClose }): React.ReactElement => {
  return (
    <div className="error-guidance-modal">
      <Modal onClose={onClose}>
        <ModalHeading id="modal-2-heading" className="bottom-border">
          Role Descriptions
        </ModalHeading>
        <div className="modal-body">
          <div className="error-guidance-container">
            <img
              id="roleDescriptionsGraphic"
              className="role-descriptions-graphic"
              src={roleDescriptionGraphic}
              alt="Role Descriptions Graphic"
              title="Role Descriptions Graphic"
            />
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

export default RoleDescriptionModal;
