/**
 * Modal detailing submission tracker iconography.
 * @packageDocumentation
 **/
import React, { useEffect, useState } from "react";

import { Button, ButtonGroup, Icon, Modal, ModalFooter, ModalHeading, Table } from "evchartstorybook";

import { ColumnDefinitions } from "../../../interfaces/column-definitions-interface";

import { PATH_COLUMN_DEFINITIONS } from "../../../utils/pathConstants";
import { ROUTE_STATIONS } from "../../../utils/routeConstants";

import "../Modal.css";
import "./SubmissionTrackerModal.css";

/**
 * type defining the props that are passed to the SubmissionTrackerModal component
 */
type SubmissionTrackerModalProps = {
  onClose: () => void;
};

/**
 * SubmissionTrackerModal
 * @param SubmissionTrackerModalProps
 * @returns the submission tracker iconography modal
 */
export const SubmissionTrackerModal: React.FC<SubmissionTrackerModalProps> = ({ onClose }): React.ReactElement => {
  /**
   * Get the api/base url and environment variables
   */
  const API_URL = import.meta.env.VITE_API_URL;
  const BASE_URL = import.meta.env.VITE_PUBLIC_URL;

  /**
   * Get id token for endpoint authorization
   */
  const id_token = localStorage.getItem("id_token");

  /**
   * styled link to stations page
   */
  const stationsLink = (
    <span>
      {"("}
      <a href={`${BASE_URL}${ROUTE_STATIONS}`} className="evchart-link">
        update your stations here
      </a>
      {")."}
    </span>
  );

  /**
   * State variable holding the definitions
   */
  const [columnDefs, setColumnDefs] = useState<ColumnDefinitions>();

  /**
   * Get the relevant definitions
   */
  useEffect(() => {
    fetch(`${API_URL}${PATH_COLUMN_DEFINITIONS}`, {
      method: "GET",
      headers: {
        table_name: "submission_tracker",
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
   * iconography for the submission tracker
   */
  const tracker_icons = [
    <Icon.TrackerBallAttention key="attention" className="st-modal" size={3} />,
    <Icon.TrackerBallSubmitted key="submitted" className="st-modal icon-overflow-visible" size={3} />,
    <Icon.TrackerBallPartialData key="some_submitted" className="st-modal icon-overflow-visible" size={3} />,
    <Icon.TrackerBallNoData key="none_submitted" className="st-modal icon-overflow-visible" size={3} />,
    <Icon.TrackerBallNoDataRequired key="not_required" className="st-modal" size={3} />,
    <Icon.TrackerBallNoDataRequiredEver key="not_applicable" className="st-modal" size={3} />,
  ];

  return (
    <div className="submission-tracker-modal">
      <Modal onClose={onClose}>
        <ModalHeading id="modal-2-heading" className="submission-tracker-modal-heading">
          Submission Tracker Guidance
        </ModalHeading>
        <div className="modal-body">
          <div className="modal-text">
            <Table fullWidth className="submission-tracker-table">
              <thead>
                <tr>
                  <th className="submission-status-header">Submission Status</th>
                  <th className="tracker-icon-header">Tracker Icon</th>
                  <th>Status Description</th>
                </tr>
              </thead>
              <tbody>
                {columnDefs?.headers.map((header, index) => (
                  <tr key={header} className="submission-tracker-table-row">
                    <td>{header}</td>
                    <td>{tracker_icons[index]}</td>
                    <td>
                      {
                        <p className="st-modal-values">
                          {columnDefs.values[index]}
                          {index === 5 && stationsLink}
                        </p>
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
            <p className="submission-tracker-disclaimer">
              Tracker is not measuring the quality of submissions, only the number of submissions. Checking submitted
              modules for quality and completeness is still recommended.
            </p>
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

export default SubmissionTrackerModal;
