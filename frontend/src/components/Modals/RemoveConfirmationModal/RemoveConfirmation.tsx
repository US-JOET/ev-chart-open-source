/**
 * Confirmation modal to remove a module.
 * @packageDocumentation
 **/
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

import { FocusTrap } from "@mui/base/FocusTrap";

import { Alert, Button, ButtonGroup, Grid, Modal, ModalHeading, ModalFooter, Spinner } from "evchartstorybook";

import { isDRUser, isSRUser } from "../../../utils/authFunctions";
import { getOrgName } from "../../../utils/getJWTInfo";
import { PATH_MODULE_REMOVE } from "../../../utils/pathConstants";
import { ROUTE_MODULE_DATA } from "../../../utils/routeConstants";

import "./RemoveConfirmation.css";
import "../Modal.css";

/**
 * Interface defining the props that are passed to the RemoveConfirmationModal component
 */
interface RemoveConfirmationModalModalProps {
  moduleName: string;
  year: string;
  subRecipient: string | null;
  moduleType: string;
  moduleStatus: string;
  updatedBy: string;
  uploadId: string;
  onClose: () => void;
}

/**
 * RemoveConfirmationModal
 * @param RemoveConfirmationModalModalProps
 * @returns the remove module confirmation modal
 */
export const RemoveConfirmationModal: React.FC<RemoveConfirmationModalModalProps> = ({
  moduleName,
  year,
  subRecipient,
  moduleType,
  moduleStatus,
  updatedBy,
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
   * Get id token for endpoint authorization
   */
  const id_token = localStorage.getItem("id_token");

  /**
   * State variables
   */
  const [showSpinner, setShowSpinner] = useState<boolean>(false);

  /**
   * Function tied to remove module button
   */
  const handleRemove = () => {
    setShowSpinner(true);
    const removeData = {
      upload_id: uploadId,
    };

    fetch(`${API_URL}${PATH_MODULE_REMOVE}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `${id_token}`,
      },
      body: JSON.stringify(removeData),
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
        // Allow the parent page to be refreshed always on submission of draft
        localStorage.removeItem("beenRefreshed");
        // Navigate to the tabs page with the state info

        navigate(ROUTE_MODULE_DATA, {
          state: {
            startTab: moduleStatus === "Draft" ? "drafts" : moduleStatus === "Rejected" ? "rejected" : "errors",
            showRemoveSuccessAlert: true,
            forceRefresh: true,
          },
        });
      })
      .catch((err) => {
        console.log(err);
        setShowSpinner(false);
      });
  };

  /**
   * Function to populate subrecipient information for the module upload if applicable
   * @returns the subrecipient name or "--"
   */
  const getSubrecipientLabel = (): string => {
    if (moduleStatus === "Draft") {
      return isSRUser() ? getOrgName() : "--";
    }
    if (moduleStatus === "Rejected") {
      if (isSRUser()) {
        return getOrgName();
      } else if (isDRUser() && subRecipient === null) {
        return "--";
      }
    }
    return subRecipient ? subRecipient : "--";
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
                Remove Confirmation
              </ModalHeading>
              <p>Are you sure you want to remove this data module?</p>

              <div className="remove-alert">
                <Alert type="error" headingLevel="h3" heading="This action cannot be undone.">
                  By removing the data, you will not be able to recover it.
                </Alert>
              </div>

              <Grid row className="remove-modal-field">
                <Grid col={6}>
                  <p>Module:</p>
                </Grid>
                <Grid col={6}>
                  <p className="field">{moduleName}</p>
                </Grid>
              </Grid>

              <Grid row className="remove-modal-field">
                <Grid col={6}>
                  <p>Reporting Year:</p>
                </Grid>
                <Grid col={6}>
                  <p className="field">{year}</p>
                </Grid>
              </Grid>

              <Grid row className="remove-modal-field">
                <Grid col={6}>
                  <p>Submission Type:</p>
                </Grid>
                <Grid col={6}>
                  <p className="field">{moduleType}</p>
                </Grid>
              </Grid>

              <Grid row className="remove-modal-field">
                <Grid col={6}>
                  <p>Subrecipient/ Contractor:</p>
                </Grid>
                <Grid col={6}>
                  <p className="field">{getSubrecipientLabel()}</p>
                </Grid>
              </Grid>

              <Grid row className="remove-modal-field">
                <Grid col={6}>
                  <p>Last Updated By:</p>
                </Grid>
                <Grid col={6}>
                  <p className="field">{updatedBy}</p>
                </Grid>
              </Grid>

              <ModalFooter>
                <ButtonGroup className="modal-button-group">
                  <Button type="button" onClick={handleRemove}>
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

export default RemoveConfirmationModal;
