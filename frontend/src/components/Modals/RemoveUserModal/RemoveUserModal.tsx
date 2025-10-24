/**
 * Modal to remove a user from an organization.
 * @packageDocumentation
 **/
import React from "react";
import { useNavigate } from "react-router";

import { Button, ButtonGroup, Modal, ModalFooter } from "evchartstorybook";

import { PATH_USERS } from "../../../utils/pathConstants";

import "../Modal.css";

/**
 * Interface defining the props that are passed to the RemoveUserModal component
 */
interface RemoveUserModalProps {
  email: string;
  onClose: () => void;
}

/**
 * RemoveUserModal
 * @param RemoveUserModalProps
 * @returns the remove user modal
 */
export const RemoveUserModal: React.FC<RemoveUserModalProps> = ({ email, onClose }): React.ReactElement => {
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
   * Function tied to remove user button
   */
  const removeUser = () => {
    const submitData = {
      email: email,
      action: "remove",
    };

    fetch(`${API_URL}${PATH_USERS}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `${access_token}`,
      },
      body: JSON.stringify(submitData),
    })
      .then(response => {
        if (response.ok) {
          // Set a local storage item to check on refresh
          localStorage.setItem("userRemoved", "true");
          // Refresh the page
          navigate(0);
        } else {
          throw response;
        }
      })
      .catch((err) => {
        localStorage.setItem("patchUserFailed", "true");
        console.log(err.message);
      });
  };

  return (
    <div className="remove-user-modal">
      <Modal onClose={onClose} aria-labelledby="remove-user-heading" aria-describedby="remove-user-description">
        <div className="modal-body">
          <div className="modal-subheader">Are you sure you want to remove this user from your organization?</div>
          <div className="modal-body-text">
            Removing this user will prevent them from uploading and handling data on your organization's behalf.
          </div>
        </div>
        <ModalFooter id="removeUserModalFooter">
          <ButtonGroup>
            <Button
              onClick={() => {
                removeUser();
              }}
              type="button"
            >
              Remove
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

export default RemoveUserModal;
