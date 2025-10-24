/**
 * Table containing the details of an organization's module submissions.
 * Imported into the Module Data view.
 * @packageDocumentation
 **/
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router";

import { Actions, Button, Chip, Icon, Grid, GridContainer, Table, Select, Tooltip, Pagination } from "evchartstorybook";

import { SortState } from "../../interfaces/ui-components-interfaces";

import { isSRUser, isDRUser, isJOUser, isAdmin } from "../../utils/authFunctions";
import { FeatureFlagEnum, getFeatureFlagValue, getFeatureFlagList } from "../../utils/FeatureToggle";
import { ROUTE_HISTORY, ROUTE_MODULE } from "../../utils/routeConstants";

import CustomLink from "../Tooltip/tooltips";

import "./SubmittalsTabTable.css";

interface ModuleInfo {
  module_name: string;
  year: string;
  module_frequency: string;
  direct_recipient: string;
  sub_recipient: string;
  submission_status: string;
  updated_on: string;
  updated_by: string;
  upload_id: string;
}

/**
 * Interface defining the props that are passed to the SubmittalsTabTable component
 */
interface SubmittalsTabTableProps {
  setImportModal?: () => void;
  setColumnDefinitionsModal?: () => void;
  setErrorDownloadModal?: () => void;
  setErrorGuidanceModal?: () => void;
  setCurrUploadId: (id: string) => void;
  setCurrModuleName?: (id: string) => void;
  setCSVModal: () => void;
  setRemoveModalData?: (data: ModuleInfo) => void;
  tab: string;
  draftsData?: Array<any>;
  pendingApprovalData?: Array<ModuleInfo>;
  submittedData?: Array<ModuleInfo>;
  rejectedData?: Array<ModuleInfo>;
  errorsData?: Array<ModuleInfo>;
  isSubmittedDataLoading: boolean;
}

export const SubmittalsTabTable: React.FC<SubmittalsTabTableProps> = ({
  setImportModal,
  setColumnDefinitionsModal,
  setErrorDownloadModal,
  setErrorGuidanceModal,
  setCurrUploadId,
  setCurrModuleName,
  setCSVModal,
  setRemoveModalData,
  tab,
  draftsData,
  pendingApprovalData,
  submittedData,
  rejectedData,
  errorsData,
  isSubmittedDataLoading,
}): React.ReactElement => {
  /**
   * Feature flag management
   * Toggles the Remove Module Data action from the table
   */
  const [removeModuleFeatureFlag, setRemoveModuleFeatureFlag] = useState(false);

  useEffect(() => {
    /**
     * navigates users to top of page
     */
    window.scrollTo(0, 0);

    /**
     * On initial render, get the feature flag list and, using its results,
     * set the feature flag state variable.
     */
    getFeatureFlagList().then((results) => {
      setRemoveModuleFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.RemoveModule));
    });
  }, []);

  /**
   * Set navigate for refresh on modal close
   */
  const navigate = useNavigate();

  /**
   * Set the data for the table
   */
  let submitted: any = [];

  switch (tab) {
    case "all":
      submitted = draftsData?.concat(pendingApprovalData, submittedData, rejectedData, errorsData);
      break;
    case "pending-approval":
      if (pendingApprovalData !== undefined) {
        submitted = pendingApprovalData;
      }
      break;
    case "submitted":
      if (submittedData !== undefined) {
        submitted = submittedData;
      }
      break;
    case "rejected":
      if (rejectedData !== undefined) {
        submitted = rejectedData;
      }
      break;
    case "errors":
      if (errorsData !== undefined) {
        submitted = errorsData;
      }
      break;
    default:
      submitted = [];
  }

  /**
   * Handle viewing module details
   * Redirects user to the module details view
   * @param id the uuid of the module that the user has selected
   * @returns button to be rendered in the actions dropdown
   */
  const ViewDetails = (id: string) => {
    return (
      <Button type="button" onClick={() => navigate(`${ROUTE_MODULE}/${id}`)}>
        View Details
      </Button>
    );
  };

  /**
   * Handle downloading module data
   * @param id the uuid of the module that the user has selected
   * @returns button to be rendered in the actions dropdown
   */
  const DownloadDetails = (id: string) => {
    return (
      <Button type="button" onClick={() => openCSVModal(id)}>
        Download as CSV
      </Button>
    );
  };

  /**
   * Helper function to download the error report
   * @param item information about the row/module the user selected
   */
  const handleOpenDownloadErrorReport = (item: ModuleInfo) => {
    setCurrUploadId(item.upload_id);
    setCurrModuleName!(item.module_name);
    setErrorDownloadModal!();
  };

  /**
   * Handle downloading the error report
   * @param item information about the row/module the user selected
   * @returns button to be rendered in the actions dropdown
   */
  const DownloadErrorReport = (item: ModuleInfo) => {
    return (
      <>
        <Button type="button" onClick={() => handleOpenDownloadErrorReport!(item)}>
          Download Error Report
        </Button>
      </>
    );
  };

  /**
   * Handle viewing module history log
   * Redirects user to the module details history log view
   * @param id the uuid of the module that the user has selected
   * @returns button to be rendered in the actions dropdown
   */
  const ViewHistoryLog = (id: string) => {
    return (
      <Button
        type="button"
        onClick={() =>
          navigate(`${ROUTE_MODULE}/${id}${ROUTE_HISTORY}`, {
            state: {
              historyLogView: true,
            },
          })
        }
      >
        View History Log
      </Button>
    );
  };

  /**
   * Handle removing module data
   * Opens the modal to remove module data
   * @param item information about the row/ module user selected
   * @returns button to be rendered in the actions dropdown
   */
  const RemoveModuleData = (item: ModuleInfo) => {
    return (
      <Button type="button" onClick={() => setRemoveModalData!(item)}>
        Remove
      </Button>
    );
  };

  /**
   * Open the csv download modal
   * @param id the uuid of the module that the user has selected
   */
  const openCSVModal = (id: string) => {
    setCurrUploadId(id);
    setCSVModal();
  };

  /**
   * Manages the default sort for rows of data in the submittals tab table
   */
  const initialSortState: SortState<ModuleInfo> = {
    column: "updated_on",
    direction: "desc",
  };
  const [sortState, setSortState] = useState(initialSortState);

  /**
   * Set the columns for the table
   */
  const columnHeaders: { key: keyof ModuleInfo; label: string }[] = [
    { key: "module_name", label: "Module" },
    { key: "year", label: "Reporting Year" },
    { key: "module_frequency", label: "Type" },
  ];

  if (isDRUser()) {
    columnHeaders.push({ key: "sub_recipient", label: "Subrecipient/ Contractor" });
    if (isAdmin()) {
      columnHeaders.push({ key: "submission_status", label: "Status" });
    }
    columnHeaders.push(
      { key: "updated_on", label: "Updated On" },
      { key: "updated_by", label: "Updated By" },
      { key: "upload_id", label: "Upload ID" },
    );
  } else if (isSRUser()) {
    columnHeaders.push({ key: "direct_recipient", label: "Direct Recipient" });
    if (isAdmin()) {
      columnHeaders.push({ key: "submission_status", label: "Status" });
    }
    columnHeaders.push(
      { key: "updated_on", label: "Updated On" },
      { key: "updated_by", label: "Updated By" },
      { key: "upload_id", label: "Upload ID" },
    );
  } else if (isJOUser()) {
    columnHeaders.push(
      { key: "direct_recipient", label: "Direct Recipient" },
      { key: "sub_recipient", label: "Subrecipient/ Contractor" },
      { key: "updated_on", label: "Updated On" },
      { key: "upload_id", label: "Upload ID" },
    );
  }

  /**
   * Change the sort state from user selection
   * @param column the selected column
   */
  const toggleSort = (column: keyof ModuleInfo) => {
    if (
      column === "module_name" ||
      column === "year" ||
      column === "module_frequency" ||
      column === "direct_recipient" ||
      column === "submission_status" ||
      column === "updated_on" ||
      column === "updated_by" ||
      column === "upload_id"
    ) {
      setSortState((prevState) => ({
        column,
        direction: prevState.column === column && prevState.direction === "asc" ? "desc" : "asc",
      }));
    }
  };

  /**
   * Sort data in table based on the sort state
   */
  const sortedData = [...submitted].sort((a: ModuleInfo, b: ModuleInfo) => {
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
   * Manage pagination
   */
  const [current, setCurrentPage] = useState<number>(1);
  const [itemsPerPage, setItemsPerPage] = useState<number>(25);

  const numberOfPages = sortedData !== undefined ? Math.ceil(sortedData.length / itemsPerPage) : 0;
  const totalItems = sortedData !== undefined ? sortedData.length : 0;

  const startIndex = (Number(current) - 1) * Number(itemsPerPage);
  const endIndex = Number(startIndex) + Number(itemsPerPage);
  const visibleData = sortedData !== undefined ? sortedData.slice(startIndex, endIndex) : [];

  /**
   * Handle user selecting the 'Next' paginated page.
   * Increments the current page number by one.
   */
  const handleNext = () => {
    const nextPage = current + 1;
    setCurrentPage(nextPage);
  };

  /**
   * Handle user selecting the 'Previous' paginated page.
   * Decrements the current page number by one.
   */
  const handlePrevious = () => {
    const prevPage = current - 1;
    setCurrentPage(prevPage);
  };

  /**
   * Handle user moving between paginated pages
   * @param event html mouse event
   * @param pageNum the selected page number
   */
  const handlePageNumber = (event: React.MouseEvent<HTMLButtonElement>, pageNum: number) => {
    setCurrentPage(pageNum);
  };

  /**
   * Update the number of pages based on user selection
   * @param event the selected number of items per page
   */
  const updateNumPages = (event: any) => {
    setItemsPerPage(event);
    setCurrentPage(1);
  };

  const formattedDate = (date: string) => {
    if (!date) {
      return "";
    }
    const splitDate = date.split(" ");
    return (
      <>
        {splitDate[0]}
        <br />
        {splitDate.slice(1).map((item) => (
          <span key={item}>{" " + item}</span>
        ))}
      </>
    );
  };

  const formattedLabel = (label: string) => {
    const splitLabel = label.split(" ");
    if (splitLabel.length < 2) {
      return label;
    } else {
      return (
        <div>
          {splitLabel[0]} <br />
          {splitLabel[1]}
        </div>
      );
    }
  };

  /**
   * Render the appropriately styled module chip
   *
   * @param status module status (Pending Approval, Submitted, Approved, Rejected,
   * Draft, Error, Processing)
   *
   * @returns the styled chip
   */
  const ModuleChip = (status: string): React.ReactElement => {
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
      case "Processing":
        moduleChip = (
          <Tooltip
            label={"This draft is uploading to the system and will be available to review soon."}
            asCustom={CustomLink}
          >
            <Chip type="processing">
              Uploading
              <br />
              Draft
            </Chip>
          </Tooltip>
        );
        break;
    }
    return moduleChip;
  };

  /**
   * Function to render a table body component when there is a submission data to display
   * in the table.
   * @returns table body component
   */
  function noDataView(): React.ReactNode {
    return (
      <tbody data-testid="noDataAddDraft">
        <tr>
          <td colSpan={12}>
            <Grid col={12} className="no-data-add-draft">
              {isJOUser() || !isAdmin() ? (
                <p>No Submitted Module Data</p>
              ) : (
                <p>
                  <span className="upload-module-data-modal-link" onClick={setImportModal}>
                    Upload module data
                  </span>{" "}
                  to get started
                </p>
              )}
            </Grid>
          </td>
        </tr>
      </tbody>
    );
  }

  /**
   * Function to determine which arrow (up, down, double) to render based on current sort state
   * @param column the label for the column being checked
   * @returns the appropriate arrow based on current sort state
   */
  const renderSortArrow = (column: string) => {
    if (
      column === "module_name" ||
      column === "year" ||
      column === "module_frequency" ||
      column === "direct_recipient" ||
      column === "submission_status" ||
      column === "updated_on" ||
      column === "updated_by" ||
      column === "upload_id"
    ) {
      if (column === sortState.column) {
        if (sortState.direction === "asc") {
          return <Icon.ArrowUpward className="sort-icon-submitted" />;
        } else {
          return <Icon.ArrowDownward className="sort-icon-submitted" />;
        }
      }
      return <Icon.SortArrow className="sort-icon-submitted" />;
    }
  };

  /**
   * Get the available actions for a module
   * @param item the module information from the current row
   * @returns the set of actions available to users
   */
  const getActions = (item: any) => {
    if (isDRUser() || isSRUser()) {
      const actions = [
        {
          name: "ViewDetails",
          component: ViewDetails(item.upload_id),
        },
        {
          name: "Download",
          component: DownloadDetails(item.upload_id),
        },
      ];
      if (isAdmin()) {
        actions.push({
          name: "View History Log",
          component: ViewHistoryLog(item.upload_id),
        });
      }

      const isRejectedModule = (): boolean =>
        tab === "rejected" || (tab === "all" && item.submission_status === "Rejected");

      const isDraftModule = (): boolean => tab === "all" && item.submission_status === "Draft";

      /**
       * Allows SR admins to remove Rejected modules.
       * Allows DR and SR admins to remove Draft modules.
       */
      if (((isRejectedModule() && isSRUser()) || isDraftModule()) && removeModuleFeatureFlag) {
        actions.push({
          name: "RemoveModuleData",
          component: RemoveModuleData(item),
        });
      }
      return (
        <Actions
          item={{
            options: actions,
          }}
        />
      );
    } else {
      return (
        <Actions
          item={{
            options: [
              {
                name: "ViewDetails",
                component: ViewDetails(item.upload_id),
              },
              {
                name: "Download",
                component: DownloadDetails(item.upload_id),
              },
            ],
          }}
        />
      );
    }
  };

  /**
   * Get the error actions for a module
   * @param item the module information from the current row
   * @returns the set of actions available to users when the submission status is "Error"
   */
  const getDownloadErrorReport = (item: any) => {
    const actions = [
      {
        name: "Download Error Report",
        component: DownloadErrorReport(item),
      },
    ];

    if (removeModuleFeatureFlag) {
      actions.push({
        name: "RemoveModuleData",
        component: RemoveModuleData(item),
      });
    }

    return (
      <Actions
        item={{
          options: actions,
        }}
      />
    );
  };

  function tableData(): React.ReactNode {
    return (
      <tbody data-testid="submittedData">
        {visibleData.map((item, index) => (
          <tr className="submitted-row" data-testid="submittedRow" key={index}>
            <th className="module-data" scope="row">
              {item.submission_status === "Processing" || item.submission_status === "Error" ? (
                <span>{item.module_name}</span>
              ) : (
                <a className="module-to-data-hyperlink" href={`${ROUTE_MODULE}/${item.upload_id}`}>
                  {item.module_name}
                </a>
              )}
            </th>
            <td> {item.year} </td>
            <td> {item.module_frequency} </td>
            {(isSRUser() || isJOUser()) && <td> {item.direct_recipient} </td>}
            {(isDRUser() || isJOUser()) && <td> {item.sub_recipient} </td>}
            {(isDRUser() || isSRUser()) && isAdmin() && (
              <td className={item.submission_status} style={{ whiteSpace: "nowrap" }}>
                {ModuleChip(item.submission_status)}
              </td>
            )}
            <td> {formattedDate(item.updated_on)}</td>
            {(isDRUser() || isSRUser()) && <td> {item.updated_by} </td>}
            <td> {item.upload_id} </td>
            {item.submission_status === "Error" ? (
              <td>{getDownloadErrorReport(item)}</td>
            ) : item.submission_status === "Processing" ? (
              <td>
                <span>--</span>
              </td>
            ) : (
              <td>{getActions(item)}</td>
            )}
          </tr>
        ))}
      </tbody>
    );
  }

  /**
   * Function to render the pagination options at the top of the table. Allows
   * the user to select the number of rows to display in the table.
   * @returns Select dropdown with number of row options
   */
  function tablePagination() {
    return (
      <GridContainer className="pagination-info">
        <Grid row className="pagination-info-row">
          <div className="pagination-info-dropdown">
            {sortedData.length > 10 ? (
              <>
                <p className="pagination-info-row-count">
                  {startIndex + 1}-{endIndex > totalItems ? totalItems : endIndex} of {totalItems} rows
                </p>
                <p className="pagination-info-row-per-page">Rows per page:</p>
                <Select
                  id="submittalsSelectItemsPerPage"
                  name="submittals-select-items-per-page"
                  title="submittals-select-items-per-page"
                  style={{ width: 90 }}
                  value={itemsPerPage}
                  onChange={(e) => updateNumPages(e.target.value)}
                >
                  <option value="10">10</option>
                  <option value="25">25</option>
                  <option value="50">50</option>
                  <option value="100">100</option>
                </Select>
              </>
            ) : (
              <div className="no-pagination" />
            )}
          </div>

          {(tab === "all" || tab === "errors") && !isJOUser() && (
            <div>
              <Button
                type="button"
                unstyled
                className="error-guidance-button"
                style={{ right: 0 }}
                onClick={setErrorGuidanceModal}
              >
                How do I read an error report?
              </Button>
            </div>
          )}

          <div>
            <Button
              type="button"
              unstyled
              className={"column-definitions-button"}
              style={{ right: 0 }}
              onClick={setColumnDefinitionsModal}
            >
              Column Definitions
            </Button>
          </div>
        </Grid>
      </GridContainer>
    );
  }

  /**
   * Render the 'Previous', 'Next', and page number buttons
   * @returns pagination buttons
   */
  function paginationButtons(): React.ReactNode {
    return (
      <GridContainer>
        <Grid row style={{ justifyContent: "center" }}>
          <Pagination
            totalPages={numberOfPages}
            pathname="management/stations"
            currentPage={current}
            onClickNext={handleNext}
            onClickPrevious={handlePrevious}
            onClickPageNumber={handlePageNumber}
          />
        </Grid>
      </GridContainer>
    );
  }

  /**
   * Render the table's header
   * @returns the table header
   */
  function tableHeader() {
    return (
      <thead className="submitted-table-header">
        <tr>
          {columnHeaders.map(({ key, label }) => (
            <th key={key} className={"submitted-table-header " + key} scope="col" data-testid={key}>
              <div className="submitted-column-header" onClick={() => toggleSort(key)}>
                {formattedLabel(label)}
                {renderSortArrow(key)}
              </div>
            </th>
          ))}
          <th className="submitted-table-header actions">Actions</th>
        </tr>
      </thead>
    );
  }

  return (
    <div id="SubmittalsTable" data-testid="SubmittalsTable">
      {tablePagination()}
      <Table striped fullWidth bordered={false} className="submitted-table">
        {tableHeader()}
        {visibleData.length === 0 && !isSubmittedDataLoading ? noDataView() : tableData()}
      </Table>
      {sortedData.length > 10 && paginationButtons()}
    </div>
  );
};

export default SubmittalsTabTable;
