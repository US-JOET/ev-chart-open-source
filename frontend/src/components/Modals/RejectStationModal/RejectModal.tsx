/**
 * Modal to reject a station.
 * @packageDocumentation
 **/
import React, { useState } from "react";
import { useNavigate } from "react-router";

import {
  Button,
  ButtonGroup,
  ErrorMessage,
  Grid,
  Modal,
  ModalHeading,
  ModalFooter,
  Spinner,
  Textarea,
} from "evchartstorybook";

import { PATH_STATION_REMOVE } from "../../../utils/pathConstants";
import { ROUTE_STATIONS } from "../../../utils/routeConstants";

import "./RejectModal.css";
import "../Modal.css";

/**
 * Interface defining the props that are passed to the RejectModal component
 */
interface RejectModalProps {
  stationUUID: string;
  stationID: string;
  authorizedSrNamesList: string[];
  nickname: string;
  address: string;
  numFederalPorts: string;
  numNonFederalPorts: string;
  onClose: () => void;
}

/**
 * RejectModal
 * @param RejectModalProps
 * @returns the reject station modal
 */
export const RejectModal: React.FC<RejectModalProps> = ({
  stationUUID,
  stationID,
  authorizedSrNamesList,
  nickname,
  address,
  numFederalPorts,
  numNonFederalPorts,
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
   * State variables
   */
  const [rejectionComments, setRejectionComments] = useState<string>("");
  const [showSpinner, setShowSpinner] = useState<boolean>(false);
  const [showCommentError, setShowCommentError] = useState<boolean>(false);
  const [remainingChars, setRemainingChars] = useState<number>(200);

  /**
   * Function tied to reject station button
   */
  const rejectModule = () => {
    setShowCommentError(false);

    if (rejectionComments.replace(/\s/g, "") !== "") {
      setShowSpinner(true);
      const removeStation = {
        station_uuid: stationUUID,
        comments: rejectionComments,
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
          navigate(ROUTE_STATIONS, {
            state: {
              rejectSuccess: true,
              authorizedSrNamesList: authorizedSrNamesList,
            },
          });
        })
        .catch((err) => {
          console.log(err);
          setShowSpinner(false);
        });
    } else {
      // Validation
      setShowCommentError(true);
    }
  };

  /**
   * Event tied to typing comments
   * @param comments the comments being typed
   */
  const updateRejectionField = (comments: string) => {
    setRejectionComments(comments);
    setRemainingChars(200 - comments.length);
  };

  return (
    <div className="reject-modal">
      <Modal onClose={onClose} aria-labelledby="modal-1-heading" aria-describedby="modal-1-description">
        {showSpinner ? (
          <div className="spinner-modal-body">
            <Spinner></Spinner>
          </div>
        ) : (
          <>
            <ModalHeading id="rejectModalHeading" className="bottom-border">
              Reject & Do Not Add Station
            </ModalHeading>
            <div className="modal-body">
              <div className="modal-subheader">Station Information</div>
              <Grid row className="reject-modal-field">
                <Grid col={7} className="reject-modal-label">
                  Station ID:
                </Grid>
                <Grid className="reject-modal-value">{stationID}</Grid>
              </Grid>
              <Grid row className="reject-modal-field">
                <Grid col={7} className="reject-modal-label">
                  Station Nickname:
                </Grid>
                <Grid className="reject-modal-value">{nickname}</Grid>
              </Grid>
              <Grid row className="reject-modal-field">
                <Grid col={7} className="reject-modal-label">
                  Station Address:
                </Grid>
                <Grid className="reject-modal-value">{address}</Grid>
              </Grid>
              <Grid row className="reject-modal-field">
                <Grid col={7} className="reject-modal-label">
                  Number of Federally Funded Ports:
                </Grid>
                <Grid className="reject-modal-value">{numFederalPorts}</Grid>
              </Grid>
              <Grid row className="reject-modal-field">
                <Grid col={7} className="reject-modal-label">
                  Number of Non-Federally Funded Ports:
                </Grid>
                <Grid className="reject-modal-value">
                  {String(numNonFederalPorts).trim() === "" || numNonFederalPorts === null ? "N/A" : numNonFederalPorts}
                </Grid>
              </Grid>

              <div className="reject-modal-comments">
                <p className="reject-comments-label required-field">Feedback from Reviewer</p>
                <Textarea
                  id="rejectionComments"
                  name="rejection-comments"
                  maxLength={200}
                  className={showCommentError ? "rejection-comment-box usa-input--error" : "rejection-comment-box"}
                  onChange={(e) => {
                    updateRejectionField(e.target.value);
                  }}
                />
                <p className="rejection-comments-counter">Characters Remaining: {remainingChars}/200</p>
                {showCommentError && <ErrorMessage>This field is required</ErrorMessage>}
              </div>
            </div>
            <ModalFooter id="rejectModalFooter">
              <ButtonGroup>
                <Button
                  onClick={() => {
                    rejectModule();
                  }}
                  type="button"
                >
                  Reject
                </Button>
                <Button onClick={onClose} type="button" unstyled className="padding-105 text-center">
                  Cancel
                </Button>
              </ButtonGroup>
            </ModalFooter>
          </>
        )}
      </Modal>
    </div>
  );
};

export default RejectModal;
