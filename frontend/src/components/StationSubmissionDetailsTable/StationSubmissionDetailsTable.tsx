/**
 * Table containing the details of a single station's module submissions. Imported into
 * the Station Submission Details view.
 * @packageDocumentation
 **/
import React, { useState } from "react";

import { Button, Grid, Icon, Table } from "evchartstorybook";

import { SortState } from "../../interfaces/ui-components-interfaces";

import { ROUTE_MODULE } from "../../utils/routeConstants";

import { ModuleChip } from "../ModuleChip/ModuleChip";
import { StationSubmissionDetail } from "../../containers/StationSubmissionDetails/StationSubmissionDetails";

import "./StationSubmissionDetailsTable.css";

/**
 * Interface defining the props that are passed to the StationSubmissionDetailsTable component
 */
interface StationSubmissionDetailsTableProps {
  /**
   * List of submission details for a given station to be displayed in the table
   */
  stationSubmissionDetails: StationSubmissionDetail[];
  /**
   * Reporting period label
   * (Quarter 1, Quarter 2, Quarter 3, Quarter 4, Annual, or One-Time)
   */
  reportingPeriodColumnLabel: string;
  /**
   * Function to open the column definitions modal
   */
  setColumnDefinitionsModal: () => void;
}

type StationSubmissionDetailsTableSortState = SortState<StationSubmissionDetail>;

export const StationSubmissionDetailsTable: React.FC<StationSubmissionDetailsTableProps> = ({
  stationSubmissionDetails,
  reportingPeriodColumnLabel,
  setColumnDefinitionsModal,
}): React.ReactElement => {
  /**
   * Manages the default sort for rows of data in the Station Submission Details table
   */
  const initialSortState: StationSubmissionDetailsTableSortState = {
    column: "updated_on",
    direction: "desc",
  };
  const [sortState, setSortState] = useState(initialSortState);

  /**
   * Set the columns for the table
   */
  const columnHeaders: {
    key: keyof StationSubmissionDetail;
    label: string;
  }[] = [
    { key: "module_name", label: `${reportingPeriodColumnLabel} Modules` },
    { key: "sub_recipient", label: "Subrecipients/Contractors" },
    { key: "submission_status", label: "Status" },
    { key: "updated_on", label: "Updated On" },
    { key: "upload_id", label: "Upload ID" },
  ];

  /**
   * Sort data in table based on the sort state
   */
  const sortedData = [...stationSubmissionDetails].sort((a: StationSubmissionDetail, b: StationSubmissionDetail) => {
    const direction = sortState.direction === "asc" ? 1 : -1;
    let columnA, columnB;
    if (sortState.column === "updated_on") {
      columnA = new Date(a[sortState.column]);
      columnB = new Date(b[sortState.column]);
    } else {
      columnA = a[sortState.column].toUpperCase();
      columnB = b[sortState.column].toUpperCase();
    }
    if (columnA < columnB) return -direction;
    if (columnA > columnB) return direction;
    return 0;
  });

  /**
   * Function to determine which arrow (up, down, double) to render based on current sort state
   * @param column the label for the column being checked
   * @returns the appropriate arrow based on current sort state
   */
  const RenderSortArrow = ({ column }: { column: keyof StationSubmissionDetail }) => {
    if (column === sortState.column) {
      if (sortState.direction === "asc") {
        return <Icon.ArrowUpward className="sort-icon-submitted" />;
      } else {
        return <Icon.ArrowDownward className="sort-icon-submitted" />;
      }
    }
    return <Icon.SortArrow className="sort-icon-submitted" />;
  };

  /**
   * Change the sort state from user selection
   * @param column the selected column
   */
  const toggleSort = (column: keyof StationSubmissionDetail) => {
    setSortState((prevState) => ({
      column,
      direction: prevState.column === column && prevState.direction === "asc" ? "desc" : "asc",
    }));
  };

  return (
    <div id="StationSubmissionDetailsTable" data-testid="StationSubmissionDetailsTable">
      <div className="station-submission-details__column-definitions">
        <Button type="button" unstyled className="column-definitions-button" onClick={setColumnDefinitionsModal}>
          Column Definitions
        </Button>
      </div>
      <Table striped fullWidth bordered={false} className="station-submission-details-table">
        <thead>
          <tr>
            {columnHeaders.map(({ key, label }) => (
              <th className={key} key={key} scope="col" data-testid={key}>
                <div className="submitted-column-header" onClick={() => toggleSort(key)}>
                  {label}
                  <RenderSortArrow column={key} />
                </div>
              </th>
            ))}
          </tr>
        </thead>
        {sortedData.length === 0 ? (
          <tbody data-testid="noDataTable">
            <tr>
              <td colSpan={12} className="no-data-table-cell">
                <Grid col={12} className="no-data-table-cell__content">
                  No data modules match selected parameters.
                </Grid>
              </td>
            </tr>
          </tbody>
        ) : (
          <tbody data-testid="stationSubmissionDetailsData">
            {sortedData.map((item, index) => (
              <tr className="station-submission-details-row" data-testid="stationSubmissionDetailsRow" key={index}>
                <th scope="row">
                  {item.submission_status === "Processing" || item.submission_status === "Error" ? (
                    <span>{item.module_name}</span>
                  ) : (
                    <a className="module-to-data-hyperlink" href={`${ROUTE_MODULE}/${item.upload_id}`}>
                      {item.module_name}
                    </a>
                  )}
                </th>
                <td>{item.sub_recipient}</td>
                <td>
                  <ModuleChip submission_status={item.submission_status} />
                </td>
                <td>{item.updated_on}</td>
                <td>{item.upload_id}</td>
              </tr>
            ))}
          </tbody>
        )}
      </Table>
    </div>
  );
};

export default StationSubmissionDetailsTable;
