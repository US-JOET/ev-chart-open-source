/**
 * Modal to detail submission status information.
 * @packageDocumentation
 **/
import React, { useEffect, useState } from "react";

import { Button, ButtonGroup, Chip, Modal, ModalFooter, ModalHeading, Table } from "evchartstorybook";

import { ColumnDefinitions } from "../../../interfaces/column-definitions-interface";

import { isDRUser, isJOUser } from "../../../utils/authFunctions";
import { PATH_COLUMN_DEFINITIONS } from "../../../utils/pathConstants";

import "./SubmissionStatusModal.css";
import "../Modal.css";

interface SubmissionStatusModalProps {
  onClose: () => void;
}

export const SubmissionStatusModal: React.FC<SubmissionStatusModalProps> = ({ onClose }): React.ReactElement => {
  /**
   * Get the api url from the environment variables
   */
  const API_URL = import.meta.env.VITE_API_URL;

  /**
   * Get id token for endpoint authorization
   */
  const id_token = localStorage.getItem("id_token");

  /**
   * State variable to hold the column definitions text
   */
  const [columnDefs, setColumnDefs] = useState<ColumnDefinitions>();

  /**
   * Get the column definitions from API
   */
  useEffect(() => {
    const getColumnDefinitionsTableName = (): string => {
      if (isJOUser()) {
        return "submission_status_jo";
      } else if (isDRUser()) {
        return "submission_status_dr";
      } else {
        return "submission_status_sr";
      }
    };

    fetch(`${API_URL}${PATH_COLUMN_DEFINITIONS}`, {
      method: "GET",
      headers: {
        table_name: getColumnDefinitionsTableName(),
        Authorization: `${id_token}`,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        setColumnDefs(data);
      })
      .catch((err) => {
        console.log(err.message);
      });
  }, []);

  /**
   * Function to get the appropriate icon based on status
   * @param status the status of the submission
   * @returns the styled chip
   */
  const getIcon = (status: string) => {
    let moduleChip: React.ReactElement;
    switch (status) {
      case "Pending Approval":
      default:
        moduleChip = (
          <Chip type="warning">
            Pending
            <br />
            Approval
          </Chip>
        );
        break;
      case "Submitted":
        moduleChip = <Chip type="success">Submitted</Chip>;
        break;
      case "Approved":
        moduleChip = <Chip type="success">Approved</Chip>;
        break;
      case "Rejected":
        moduleChip = <Chip type="error">Rejected</Chip>;
        break;
      case "Draft":
        moduleChip = <Chip type="info">Draft</Chip>;
        break;
      case "Error":
        moduleChip = <Chip type="error">Error</Chip>;
        break;
      case "Uploading Draft":
        moduleChip = (
          <Chip type="processing">
            Uploading
            <br />
            Draft
          </Chip>
        );
        break;
    }
    return moduleChip;
  };

  return (
    <div className="submission-status-modal">
      <Modal onClose={onClose}>
        <ModalHeading id="modal-2-heading" className="submission-status-modal-heading">
          Module Submission Statuses
        </ModalHeading>
        <div className="modal-body">
          <div className="modal-text">
            <Table fullWidth className="submission-status-table">
              <thead>
                <tr>
                  <th className="submission-status-header">Submission Status</th>
                  <th className="tracker-icon-header">Status Pill</th>
                  <th>Status Description</th>
                </tr>
              </thead>
              <tbody>
                {columnDefs?.headers.map((header, index) => (
                  <tr key={header} className="submission-tracker-table-row">
                    <td>{header}</td>
                    <td>{getIcon(columnDefs?.headers[index])}</td>
                    <td>{columnDefs.values[index]}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </div>
        </div>
        <ModalFooter>
          <ButtonGroup>
            <Button onClick={() => onClose()} type="button">
              Close
            </Button>
          </ButtonGroup>
        </ModalFooter>
      </Modal>
    </div>
  );
};

export default SubmissionStatusModal;
