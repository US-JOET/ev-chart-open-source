/**
 * Confirmation modal for an SR creating a station.
 * @packageDocumentation
 **/
import React, { useState } from "react";

import { FocusTrap } from "@mui/base/FocusTrap";

import {
  Alert,
  Button,
  ButtonGroup,
  Checkbox,
  Grid,
  Modal,
  ModalHeading,
  ModalFooter,
  Spinner,
} from "evchartstorybook";

import { StationAddNew } from "../../../interfaces/Stations/stations-interface";

import "../Modal.css";
import "./SRAddStationModal.css";

/**
 * Interface defining the props that are passed to the SubmitModuleModal component
 */
interface SRAddsStationModalProps {
  stationValues: StationAddNew;
  directRecipient: string;
  handleAddStation: () => void;
  onClose: () => void;
}

/**
 * SubmitModuleModal
 * @param SRAddsStationModalProps
 * @returns the modal for SRs adding a station
 */
export const SubmitModuleModal: React.FC<SRAddsStationModalProps> = ({
  stationValues,
  directRecipient,
  handleAddStation,
  onClose,
}): React.ReactElement => {
  /**
   * State variables
   */
  const [submitDisabled, setSubmitDisabled] = useState(true);
  const [showSpinner, setShowSpinner] = useState<boolean>(false);

  /**
   * Confirmation statement to be rendered on the modal
   */
  const confirmationStatement =
    'I confirm that all station information is accurate. The station and authorization to submit data on behalf of this station will be "pending approval" until the direct recipient reviews and adds the station.';

  /**
   * Handle toggling confirm checkbox
   */
  const handleCheckboxChange = () => {
    setSubmitDisabled((prevChecked) => !prevChecked);
  };

  /**
   * Handle SR clicking add station, set spinner while processing
   */
  const clickAddStation = () => {
    setShowSpinner(true);
    handleAddStation();
  };

  /**
   * Fields of information to iterate over in the modal
   */
  const stationFields = ["Direct Recipient", "Station Nickname", "Station ID"];
  const stationInputValues = [directRecipient, stationValues.nickname, stationValues.station_id];

  return (
    <FocusTrap open>
      <div tabIndex={-1}>
        <Modal onClose={onClose}>
          {showSpinner ? (
            <div className="spinner-modal-body">
              <Spinner></Spinner>
            </div>
          ) : (
            <>
              <ModalHeading id="addStationModalHeading" className="bottom-border">
                Confirm Direct Recipient and Submit Station for Approval
              </ModalHeading>
              <Alert type="warning" headingLevel="h3" className="confirm-recipient-alert">
                Please confirm you have selected the correct Direct Recipient before submitting the station for approval
              </Alert>
              <Grid row>
                <Grid col>
                  {stationFields.map((fieldName, index) => (
                    <div key={index} className="station-field">
                      {fieldName}:
                    </div>
                  ))}
                </Grid>
                <Grid col>
                  {stationInputValues.map((stationValue, index) => (
                    <div key={index} className="station-input-value">
                      {stationValue}
                    </div>
                  ))}
                </Grid>
              </Grid>
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
                  <Button type="button" disabled={submitDisabled} onClick={clickAddStation}>
                    Confirm & Submit Station for Approval
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

export default SubmitModuleModal;
