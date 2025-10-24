/**
 * Column Definitions modal.
 * @packageDocumentation
 **/
import React, { useEffect, useState } from "react";

import { Modal, ModalHeading } from "evchartstorybook";

import { ColumnDefinitions } from "../../../interfaces/column-definitions-interface";

import { PATH_COLUMN_DEFINITIONS } from "../../../utils/pathConstants";

import "../Modal.css";

/**
 * Interface defining the props for the ColumnDefinitionsModal
 */
interface ColumnDefinitionsModalProps {
  table_name: string;
  onClose: () => void;
}

/**
 * ColumnDefinitionsModal
 * @param ColumnDefinitionsModalProps
 * @returns the column definitions modal
 */
export const ColumnDefinitionsModal: React.FC<ColumnDefinitionsModalProps> = ({
  onClose,
  table_name,
}): React.ReactElement => {
  /**
   * Get the api url from the environment variables
   */
  const API_URL = import.meta.env.VITE_API_URL;

  /**
   * Get access token for endpoint authorization
   */
  const id_token = localStorage.getItem("id_token");

  /**
   * State variable to hold the column definitions text
   */
  const [columnDefs, setColumnDefs] = useState<ColumnDefinitions>();

  /**
   * useEffect to fetch the relevant column defs based on table name
   */
  useEffect(() => {
    fetch(`${API_URL}${PATH_COLUMN_DEFINITIONS}`, {
      method: "GET",
      headers: {
        table_name: table_name,
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
  }, [table_name]);

  return (
    <div className="cancel-modal">
      <Modal onClose={onClose}>
        <ModalHeading id="modal-2-heading">Column Definitions</ModalHeading>
        <div className="modal-body">
          <div className="modal-text">
            {columnDefs?.headers.map((header, index) => (
              <div key={header} className="column-definition-item">
                <span className="column-heading"> {header}: </span> {columnDefs.values[index]}
              </div>
            ))}
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default ColumnDefinitionsModal;
