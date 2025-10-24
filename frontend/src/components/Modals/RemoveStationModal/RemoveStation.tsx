/**
 * Confirmation modal to remove a station.
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

import { PATH_STATION_REMOVE } from "../../../utils/pathConstants";
import { ROUTE_STATION_ID } from "../../../utils/routeConstants";

import "./RemoveStation.css";
import "../Modal.css";

/**
 * Interface defining the props that are passed to the RemoveStationModalProps component
 */
interface RemoveStationModalProps {
  nickname: string;
  station_uuid: string;
  station_id: string;
  setSuccessRemove: () => void;
  onClose: () => void;
}

/**
 * RemoveStationModal
 * @param RemoveStationModalProps
 * @returns the remove station confirmation modal
 */
export const RemoveStationModal: React.FC<RemoveStationModalProps> = ({
  nickname,
  station_id,
  station_uuid,
  setSuccessRemove,
  onClose,
}): React.ReactElement => {
  /**
   * Get the api/base url from the environment variables
   */
  const API_URL = import.meta.env.VITE_API_URL;
  const BASE_URL = import.meta.env.VITE_PUBLIC_URL;

  /**
   * State variables
   */
  const [confirmChecked, setConfirmedChecked] = useState(true);
  const [showSpinner, setShowSpinner] = useState<boolean>(false);

  /**
   * Handle toggling confirm checkbox
   */
  const handleConfirmedCheckboxChange = () => {
    setConfirmedChecked((prevChecked) => !prevChecked);
  };

  /**
   * Function tied to remove station button
   */
  const handleRemove = () => {
    setShowSpinner(true);
    const access_token = localStorage.getItem("access_token");
    const removeStation = {
      station_uuid: station_uuid,
    };

    fetch(`${API_URL}${PATH_STATION_REMOVE}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `${access_token}`,
      },
      body: JSON.stringify(removeStation),
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
        setSuccessRemove();
      })
      .catch((err) => {
        console.log(err);
        setShowSpinner(false);
      });
  };

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
              <ModalHeading id="removeModalHeading" className="bottom-border">
                Are you sure you want to remove this station?
              </ModalHeading>

              <div className="remove-alert">
                <Alert type="warning" headingLevel="h3" heading="Removing this station is permanent.">
                  You will not be able to access this station once it is removed. If you are looking to adjust the
                  station details,{" "}
                  <a href={`${BASE_URL}${ROUTE_STATION_ID}/${station_uuid}`} className="evchart-link">
                    {" "}
                    please review and edit your station details.
                  </a>
                </Alert>
              </div>

              <Grid row className="remove-station-field border-bottom">
                <Grid col={4}>
                  <p>Station Nickname:</p>
                </Grid>
                <Grid col={8}>
                  <p className="field">{nickname}</p>
                </Grid>
              </Grid>

              <Grid row className="remove-station-field">
                <Grid col={4}>
                  <p>Station ID:</p>
                </Grid>
                <Grid col={8}>
                  <p className="field">{station_id}</p>
                </Grid>
              </Grid>

              <div className="checkbox">
                <Checkbox
                  id="submitModuleCheckbox"
                  name="checkbox"
                  label="I confirm that I want to permanently remove this station from EV-ChART."
                  onChange={handleConfirmedCheckboxChange}
                />
              </div>

              <ModalFooter>
                <ButtonGroup className="modal-button-group">
                  <Button type="button" onClick={handleRemove} disabled={confirmChecked}>
                    Remove
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

export default RemoveStationModal;
