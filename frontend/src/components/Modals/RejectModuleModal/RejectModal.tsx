/**
 * Modal to reject a module submission.
 * @packageDocumentation
 **/
import React, { useState } from "react";
import { useNavigate } from "react-router";

import { Button, ButtonGroup, ErrorMessage, Grid, Modal, ModalHeading, ModalFooter, Textarea } from "evchartstorybook";

import { PATH_MODULE_SUBMISSION_APPROVAL } from "../../../utils/pathConstants";
import { ROUTE_MODULE_DATA } from "../../../utils/routeConstants";

import "./RejectModal.css";
import "../Modal.css";

/**
 * Interface defining the props that are passed to the RejectModal component
 */
interface RejectModalProps {
  moduleName: string;
  year: string;
  subrecipient: string;
  directRecipient: string;
  updatedOn: string;
  updatedBy: string;
  moduleType: string;
  uploadId: string;
  onClose: () => void;
}

/**
 * RejectModal
 * @param RejectModalProps
 * @returns the reject module modal
 */
export const RejectModal: React.FC<RejectModalProps> = ({
  moduleName,
  year,
  subrecipient,
  directRecipient,
  updatedOn,
  updatedBy,
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
   * State variables
   */
  const [rejectionComments, setRejectionComments] = useState<string>("");
  const [showCommentError, setShowCommentError] = useState<boolean>(false);
  const [remainingChars, setRemainingChars] = useState<number>(200);

  /**
   * Function tied to reject module button
   */
  const rejectModule = () => {
    setShowCommentError(false);

    if (rejectionComments.replace(/\s/g, "") !== "") {
      const submitData = {
        upload_id: uploadId,
        submission_status: "Rejected",
        comments: rejectionComments,
      };
      fetch(`${API_URL}${PATH_MODULE_SUBMISSION_APPROVAL}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `${access_token}`,
        },
        body: JSON.stringify(submitData),
      })
        .then(() => {
          // Allow the parent page to be refreshed always on submission of draft
          localStorage.removeItem("beenRefreshed");
          // Navigate to the tabs page with the state info
          navigate(ROUTE_MODULE_DATA, {
            state: {
              startTab: "rejected",
              showRejectedSuccessModal: true,
              moduleName: moduleName,
              moduleYear: year,
              moduleType: moduleType,
              directRecipient: directRecipient,
            },
          });
        })
        .catch((err) => {
          console.log(err.message);
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
        <ModalHeading id="rejectModalHeading" className="bottom-border">
          Reject
        </ModalHeading>
        <div className="modal-body">
          <div className="modal-subheader">{moduleName}</div>
          <Grid row className="reject-modal-field">
            <Grid col={6} className="reject-modal-label">
              Reporting Year:
            </Grid>
            <Grid col={6} className="reject-modal-value">
              {year}
            </Grid>
          </Grid>
          <Grid row className="reject-modal-field">
            <Grid col={6} className="reject-modal-label">
              Type:
            </Grid>
            <Grid col={6} className="reject-modal-value">
              {moduleType}
            </Grid>
          </Grid>
          <Grid row className="reject-modal-field">
            <Grid col={6} className="reject-modal-label">
              Subrecipient/Contractor:
            </Grid>
            <Grid col={6} className="reject-modal-value">
              {subrecipient}
            </Grid>
          </Grid>
          <Grid row className="reject-modal-field">
            <Grid col={6} className="reject-modal-label">
              Updated On:
            </Grid>
            <Grid col={6} className="reject-modal-value">
              {updatedOn}
            </Grid>
          </Grid>
          <Grid row className="reject-modal-field">
            <Grid col={6} className="reject-modal-label">
              Updated By:
            </Grid>
            <Grid col={6} className="reject-modal-value">
              {updatedBy}
            </Grid>
          </Grid>
          <Grid row className="reject-modal-field">
            <Grid col={6} className="reject-modal-label">
              Upload ID:
            </Grid>
            <Grid col={6} className="reject-modal-value">
              {uploadId}
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
      </Modal>
    </div>
  );
};

export default RejectModal;
