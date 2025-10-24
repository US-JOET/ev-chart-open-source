/**
 * Confirmation modal to remove a module.
 * @packageDocumentation
 **/
import React from "react";

import { FocusTrap } from "@mui/base/FocusTrap";

import { Alert, Button, ButtonGroup, Grid, Modal, ModalHeading, ModalFooter } from "evchartstorybook";

import "./RemovePortsConfirmation.css";
import "../Modal.css";
import { PortsInfo } from "../../../interfaces/Stations/stations-interface";

/**
 * Interface defining the props that are passed to the RemoveConfirmationModal component
 */
interface RemovePortsConfirmationModalModalProps {
  station_name: string;
  ports_to_remove: PortsInfo[];
  setIsStationFederallyFunded: React.Dispatch<React.SetStateAction<boolean | null>>;
  onConfirm: () => void;
  onClose: () => void;
}

/**
 * RemoveConfirmationModal
 * @param RemoveConfirmationModalModalProps
 * @returns the remove module confirmation modal
 */
export const RemovePortsConfirmationModal: React.FC<RemovePortsConfirmationModalModalProps> = ({
  station_name,
  ports_to_remove,
  setIsStationFederallyFunded,
  onConfirm,
  onClose,
}): React.ReactElement => {

  const handleConfirm = () => {
    setIsStationFederallyFunded(false);
    onConfirm();
  };

  const handleCancel = () => {
    setIsStationFederallyFunded(true)
    onClose();
  };

  return (
    <FocusTrap open>
      <div tabIndex={-1}>
        <Modal onClose={onClose}>
          <ModalHeading id="removeModalHeading" className="bottom-border">
            Remove Confirmation
          </ModalHeading>
          <p>Are you sure you want to change this station? Doing so will result in deletion of existing ports</p>

          <div className="remove-alert">
            <Alert type="error" headingLevel="h3" heading="This action cannot be undone.">
              By removing the ports, you will not be able to recover them.
            </Alert>
          </div>

          <Grid row className="remove-modal-field">
            <Grid col={6}>
              <p>Station:</p>
            </Grid>
            <Grid col={6}>
              <p className="field">{station_name}</p>
            </Grid>
          </Grid>

          {ports_to_remove.map((ports) => (
            <Grid row className="remove-modal-field" key={ports.port_uuid}>
              <Grid col={6}>
                <p>Port ID:</p>
              </Grid>
              <Grid col={6}>
                <p className="field">{ports.port_id}</p>
              </Grid>
            </Grid>
          ))}
          <ModalFooter>
            <ButtonGroup className="modal-button-group">
              <Button type="button" onClick={handleConfirm}>
                Remove
              </Button>
              <Button type="button" unstyled className="padding-105 text-center" onClick={handleCancel}>
                Cancel
              </Button>
            </ButtonGroup>
          </ModalFooter>
        </Modal>
      </div>
    </FocusTrap>
  );
};

export default RemovePortsConfirmationModal;
