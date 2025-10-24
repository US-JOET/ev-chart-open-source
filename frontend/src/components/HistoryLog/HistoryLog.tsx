/**
 * History log view that is available via module details.
 * @packageDocumentation
 **/
import React, { useState, useEffect } from "react";

import { Chip, Table, Spinner } from "evchartstorybook";

import { PATH_MODULE_HISTORY_LOG } from "../../utils/pathConstants";

/**
 * Interface that defines the data for each row in the history log table
 */
interface HistoryEntry {
  updated_by: string;
  organization: string;
  updated_on: string;
  submission_status: string;
  comments: string;
}

/**
 * HistoryLogTable
 * History table shown in module data details view
 * @returns react component with the table information and header
 */
export const HistoryLogTable: React.FC = (): React.ReactElement => {
  /**
   * Get the api url from the environment variables
   */
  const API_URL = import.meta.env.VITE_API_URL;

  /**
   * Get access token for endpoint authorization
   */
  const access_token = localStorage.getItem("access_token");

  /**
   * State variables for history data and loading spinner
   */
  const [historyLogData, setHistoryLogData] = useState<HistoryEntry[]>([]);
  const [isDataLoading, setIsDataLoading] = useState(true);

  /**
   * Split the url to get module id from path
   */
  const urlParts = window.location.href.split("/");
  const uploadId = urlParts[4];

  useEffect(() => {
    fetch(`${API_URL}${PATH_MODULE_HISTORY_LOG}?upload_id=${uploadId}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `${access_token}`,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        setHistoryLogData(data);
      })
      .catch((err) => {
        console.log(err.message);
      })
      .finally(() => setIsDataLoading(false));
  }, []);

  /**
   * Set the columns for the table
   */
  const columnHeaders: { key: keyof HistoryEntry; label: string }[] = [
    { key: "updated_by", label: "Updated By" },
    { key: "organization", label: "Organization" },
    { key: "updated_on", label: "Updated On" },
    { key: "submission_status", label: "Status Change" },
    { key: "comments", label: "Comments" },
  ];

  /**
   * Sort data in the history log table based on updated_on date
   */
  const sortedData = [...historyLogData].sort((a: HistoryEntry, b: HistoryEntry) => {
    const direction = -1;
    const columnA = new Date(a["updated_on"]);
    const columnB = new Date(b["updated_on"]);
    const statusA = new String(a["submission_status"]);
    const statusB = new String(b["submission_status"]);
    if (columnA < columnB) return -direction;
    if (columnA > columnB) return direction;
    if (statusA.toUpperCase() === "PROCESSING") return -direction;
    if (statusB.toUpperCase() === "PROCESSING") return direction;
    return 0;
  });

  /**
   * Render the appropriately styled module chip
   * @param status module status (draft, processing, pending, submitted, approved, rejected)
   * @returns the styled chip
   */
  const ModuleChip = (status: string): React.ReactElement => {
    let moduleChip: React.ReactElement;
    switch (status.toUpperCase()) {
      case "DRAFT":
      default:
        moduleChip = <Chip type="info">Draft</Chip>;
        break;
      case "PROCESSING":
        moduleChip = <Chip type="processing">Uploading Draft</Chip>;
        break;
      case "PENDING":
        moduleChip = <Chip type="warning">Pending Approval</Chip>;
        break;
      case "SUBMITTED":
        moduleChip = <Chip type="success">Submitted</Chip>;
        break;
      case "APPROVED":
        moduleChip = <Chip type="success">Approved</Chip>;
        break;
      case "REJECTED":
        moduleChip = <Chip type="error">Rejected</Chip>;
        break;
    }
    return moduleChip;
  };

  return (
    <div id="HistoryLogTable" className="history-log-table" data-testid="HistoryLogTable">
      <h2>History Log</h2>
      {isDataLoading ? (
        <div className="pp-dashboard-spinner-container">
          <div className="pp-dashboard-spinner">
            <Spinner />
          </div>
        </div>
      ) : (
        <Table striped fullWidth bordered={false}>
          <thead>
            <tr>
              {columnHeaders.map(({ key, label }) => (
                <th className={key} key={key} scope="col" data-testid={key}>
                  <span>{label}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody data-testid="historyData">
            {sortedData.map((item, index) => (
              <tr className="history-log-row" data-testid="historyRow" key={index}>
                <td> {item.updated_by} </td>
                <td> {item.organization} </td>
                <td> {item.updated_on} </td>
                <td> {ModuleChip(item.submission_status)} </td>
                <td> {item.comments} </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </div>
  );
};

export default HistoryLogTable;
