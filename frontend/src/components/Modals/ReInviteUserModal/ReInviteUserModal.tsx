/**
 * Modal to resend the invitation for expired users.
 * @packageDocumentation
 **/
import React from "react";
import { useNavigate } from "react-router";

import { Alert, Button, ButtonGroup, Modal, ModalFooter, ModalHeading, Table } from "evchartstorybook";

import { PATH_USERS } from "../../../utils/pathConstants";

import "../Modal.css";

/**
 * Interface defining the props that are passed to the ReInviteUserModal component
 */
interface ReInviteUserModalProps {
  name: string;
  role: string;
  email: string;
  onClose: () => void;
}

/**
 *
 * @param ReInviteUserModal
 * @returns the reinvite user modal
 */
export const ReInviteUserModal: React.FC<ReInviteUserModalProps> = ({
  name,
  role,
  email,
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
   * Event tied to reinvite user button
   */
  const reInviteUser = () => {
    const submitData = {
      email: email,
      action: "reinvite",
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
          localStorage.setItem("userInviteResent", "true");
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
    <div className="reinvite-user-modal">
      <Modal onClose={onClose} aria-labelledby="reinvite-user-heading" aria-describedby="reinvite-user-description">
        <ModalHeading id="modal-2-heading" className="bottom-border">
          Resend Invite
        </ModalHeading>
        <Alert type="warning" className="user-alert__heading" headingLevel="h3" heading="Verify user details">
          If details are incorrect, delete this user and add a new user. User has 30 days to login to EV-ChART before
          account expires again.
        </Alert>
        <div className="modal-body">
          <div className="modal-text">
            <Table fullWidth className="submission-status-table">
              <tbody>
                <tr className="user-reinvite-info-row">
                  <td>Name:</td>
                  <td>
                    <b>{name}</b>
                  </td>
                </tr>
                <tr className="user-reinvite-info-row">
                  <td>Role:</td>
                  <td>
                    <b>{role}</b>
                  </td>
                </tr>
                <tr className="user-reinvite-info-row">
                  <td>Email:</td>
                  <td>
                    <b>{email}</b>
                  </td>
                </tr>
              </tbody>
            </Table>
          </div>
        </div>
        <ModalFooter id="reInviteUserModalFooter">
          <ButtonGroup>
            <Button
              onClick={() => {
                reInviteUser();
              }}
              type="button"
            >
              Resend Invite
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

export default ReInviteUserModal;
