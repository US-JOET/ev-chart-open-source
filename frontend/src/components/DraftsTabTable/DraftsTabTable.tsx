/**
 * The drafts tab table that renders module data in the draft state.
 * @packageDocumentation
 **/
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router";

import { Actions, Button, Chip, Icon, Grid, GridContainer, Table, Select, Tooltip, Pagination } from "evchartstorybook";

import { ModuleInfo } from "../../interfaces/ModuleData/module-info";
import { SortState } from "../../interfaces/ui-components-interfaces";

import { isSRUser, isAdmin } from "../../utils/authFunctions";
import { FeatureFlagEnum, getFeatureFlagValue, getFeatureFlagList } from "../../utils/FeatureToggle";
import { ROUTE_MODULE, ROUTE_HISTORY } from "../../utils/routeConstants";

import RemoveConfirmationModal from "../Modals/RemoveConfirmationModal/RemoveConfirmation";
import SubmissionModal from "../Modals/SubmissionModal/SubmissionModal";
import CustomLink from "../Tooltip/tooltips";

import "./DraftsTabTable.css";

/**
 * Interface defining the props that are passed to the DraftsTabTable component
 */
interface DraftsTabTableProps {
  setImportModal?: () => void;
  setColumnDefinitionsModal?: () => void;
  setCurrUploadId: (id: string) => void;
  setCSVModal: () => void;
  draftsData: Array<ModuleInfo>;
}

/**
 * DraftsTabTable
 * Table data shown in the drafts tab for module data
 * @returns the react component with the table information
 */
export const DraftsTabTable: React.FC<DraftsTabTableProps> = ({
  setImportModal,
  setColumnDefinitionsModal,
  setCurrUploadId,
  setCSVModal,
  draftsData,
}): React.ReactElement => {
  /**
   * Method for changing the location / route
   */
  const navigate = useNavigate();

  /**
   * Feature flag management
   * Toggles the remove module option on the actions dropdown
   */
  const [removeModuleFeatureFlag, setRemoveModuleFeatureFlag] = useState(false);
  useEffect(() => {
    getFeatureFlagList().then((results) => {
      setRemoveModuleFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.RemoveModule));
    });
  }, []);

  /**
   * State variables for managing open/closed for modals on page
   */
  const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
  const [isRemoveConfirmationModalOpen, setIsRemoveConfirmationModalOpen] = useState(false);

  /**
   * Information to be populated on submission modal
   */
  const [moduleName, setModuleName] = useState("");
  const [moduleYear, setModuleYear] = useState("");
  const [directRecipient, setDirectRecipient] = useState("");
  const [moduleType, setModuleType] = useState("");
  const [updatedBy, setUpdatedBy] = useState("");
  const [moduleUploadId, setModuleUploadId] = useState("");

  /**
   * Open submission modal and populate information from the selected submission
   * @param module_info the selected module to be submitted
   */
  const openSubmitModal = (module_info: any) => {
    setModuleName(module_info.module_name);
    setModuleYear(module_info.year);
    setDirectRecipient(module_info.direct_recipient);
    setModuleType(module_info.module_frequency);
    setModuleUploadId(module_info.upload_id);
    setIsSubmitModalOpen(true);
  };

  const closeSubmitModal = () => {
    setIsSubmitModalOpen(false);
  };

  /**
   * Open remove confirmation and populate information from the selected removal
   * @param module_info the selected module to be removed
   */
  const openRemoveConfirmationModal = (module_info: any) => {
    setModuleName(module_info.module_name);
    setModuleYear(module_info.year);
    setDirectRecipient(module_info.direct_recipient);
    setModuleType(module_info.module_frequency);
    setUpdatedBy(module_info.updated_by);
    setModuleUploadId(module_info.upload_id);
    setIsRemoveConfirmationModalOpen(true);
  };

  const closeRemoveConfirmationModal = () => {
    setIsRemoveConfirmationModalOpen(false);
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
   * Set the columns for the table based on user role
   */
  const columnHeaders: { key: keyof ModuleInfo; label: string }[] = [
    { key: "module_name", label: "Module" },
    { key: "year", label: "Reporting Year" },
    { key: "module_frequency", label: "Type" },
  ];
  if (isSRUser()) {
    columnHeaders.push({ key: "direct_recipient", label: "Direct Recipient" });
  }
  columnHeaders.push(
    { key: "submission_status", label: "Status" },
    { key: "updated_on", label: "Uploaded On" },
    { key: "updated_by", label: "Uploaded By" },
    { key: "upload_id", label: "Upload ID" },
  );

  /**
   * Manages the default sort for rows of data in the drafts table
   */
  const initialSortState: SortState<ModuleInfo> = {
    column: "updated_on",
    direction: "desc",
  };
  const [sortState, setSortState] = useState(initialSortState);

  /**
   * Change the sort state from user selection
   * @param column the selected column
   */
  const toggleSort = (column: keyof ModuleInfo) => {
    setSortState((prevState) => ({
      column,
      direction: prevState.column === column && prevState.direction === "asc" ? "desc" : "asc",
    }));
  };

  /**
   * Function to determine which arrow (up, down, double) to render based on current sort state
   * @param column the label for the column being checked
   * @returns the appropriate arrow based on current sort state
   */
  const renderSortArrow = (column: string) => {
    if (column === sortState.column) {
      if (sortState.direction === "asc") {
        return <Icon.ArrowUpward className="sort-icon-drafts" />;
      } else {
        return <Icon.ArrowDownward className="sort-icon-drafts" />;
      }
    }
    return <Icon.SortArrow className="sort-icon-drafts" />;
  };

  /**
   * Sort data in table based on the above sort state
   */
  const drafts = draftsData;
  const sortedData = [...drafts].sort((a: ModuleInfo, b: ModuleInfo) => {
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

  /**
   * Handle submitting module data
   * Opens the modal to submit module data
   * @param module_info information about the row/ module user selected
   * @returns button to be rendered in the actions dropdown
   */
  const SubmitModuleData = (module_info: any) => {
    return (
      <Button type="button" onClick={() => openSubmitModal(module_info)}>
        Submit Module Data
      </Button>
    );
  };

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
   * Handle viewing module history log
   * Redirects user to the module details history log view
   * @param id the uuid of the module that the user has selected
   * @returns button to be rendered in the actions dropdown
   */
  const ViewHistoryLog = (id: string) => {
    return (
      <Button type="button" onClick={() => navigate(`${ROUTE_MODULE}/${id}${ROUTE_HISTORY}`)}>
        View History Log
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
   * Handle removing module data
   * Opens the modal to remove module data
   * @param module_info information about the row/ module user selected
   * @returns button to be rendered in the actions dropdown
   */
  const RemoveModuleData = (module_info: any) => {
    return (
      <Button type="button" onClick={() => openRemoveConfirmationModal(module_info)}>
        Remove
      </Button>
    );
  };

  /**
   * Get the available actions for module in draft state
   * @param item the module information from the current row
   * @returns the set of actions available to users
   */
  const getActions = (item: ModuleInfo) => {
    const actions = [
      {
        name: "ViewDetails",
        component: ViewDetails(item.upload_id),
      },
      {
        name: "ViewHistoryLog",
        component: ViewHistoryLog(item.upload_id),
      },
      {
        name: "Download",
        component: DownloadDetails(item.upload_id),
      },
      {
        name: "SubmitModuleData",
        component: SubmitModuleData(item),
      },
    ];

    if (removeModuleFeatureFlag) {
      actions.push({
        name: "RemoveModuleData",
        component: RemoveModuleData(item),
      });
    }

    return actions;
  };

  /**
   * Format date to be split across two lines
   * @param date the date object as a string
   * @returns the date split across two lines
   */
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

  /**
   * Split column headers across two lines
   * @param label column name
   * @returns the label across two lines
   */
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
   * @param status module status (draft, processing)
   * @returns the styled chip
   */
  const ModuleChip = (status: string): React.ReactElement => {
    let moduleChip: React.ReactElement;
    switch (status) {
      case "Draft":
      default:
        moduleChip = <Chip type="info">Draft</Chip>;
        break;
      case "Processing":
        moduleChip = (
          <Tooltip
            label={"This draft is uploading to the system and will be available to review soon"}
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

  return (
    <div id="DraftsTable" data-testid="DraftsTable">
      <GridContainer className="pagination-info">
        <Grid row className="pagination-info-row">
          <div className="pagination-info-dropdown">
            {sortedData.length > 10 && (
              <>
                <p className="pagination-info-row-count">
                  {startIndex + 1}-{endIndex > totalItems ? totalItems : endIndex} of {totalItems} rows
                </p>
                <p className="pagination-info-row-per-page">Rows per page:</p>
                <Select
                  id="draftSelectItemsPerPage"
                  name="draft-select-items-per-page"
                  title="draft-select-items-per-page"
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
            )}
          </div>
          <div>
            <Button
              type="button"
              unstyled
              className="column-definitions-button"
              style={{ right: 0 }}
              onClick={setColumnDefinitionsModal}
            >
              Column Definitions
            </Button>
          </div>
        </Grid>
      </GridContainer>
      <Table striped fullWidth bordered={false} className="drafts-table">
        <thead className="drafts-table-header">
          <tr>
            {columnHeaders.map(({ key, label }) => (
              <th key={key} className={"draft-table-header " + key} scope="col" data-testid={key}>
                <div className="column-header" onClick={() => toggleSort(key)}>
                  {formattedLabel(label)}
                  {renderSortArrow(key)}
                </div>
              </th>
            ))}
            <th className="actions">Actions</th>
          </tr>
        </thead>
        {visibleData.length === 0 && isAdmin() ? (
          <tbody data-testid="noDataAddDraft">
            <tr>
              <td colSpan={12}>
                <Grid col={12} className="no-data-add-draft" style={{}}>
                  <p>
                    <span className="upload-module-data-modal-link" onClick={setImportModal}>
                      Upload module data
                    </span>{" "}
                    to get started
                  </p>
                </Grid>
              </td>
            </tr>
          </tbody>
        ) : (
          <tbody data-testid="draftsData">
            {visibleData.map((item, index) => (
              <tr className="drafts-row" data-testid="draftsRow" key={index}>
                <th className="module-data" scope="row">
                  {item.submission_status === "Draft" ? (
                    <a className="module-to-data-hyperlink" href={`${ROUTE_MODULE}/${item.upload_id}`}>
                      {item.module_name}
                    </a>
                  ) : (
                    <span>{item.module_name}</span>
                  )}
                </th>
                <td> {item.year} </td>
                <td> {item.module_frequency} </td>
                {isSRUser() && <td> {item.direct_recipient} </td>}
                <td className={item.submission_status} style={{ whiteSpace: "nowrap" }}>
                  {ModuleChip(item.submission_status)}
                </td>
                <td> {formattedDate(item.updated_on)}</td>
                <td> {item.updated_by} </td>
                <td> {item.upload_id} </td>
                <td>
                  {item.submission_status === "Draft" ? (
                    <Actions
                      item={{
                        options: getActions(item),
                      }}
                    />
                  ) : (
                    <span>--</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        )}
      </Table>
      {sortedData.length > 10 && (
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
      )}
      {isSubmitModalOpen && (
        <SubmissionModal
          onClose={closeSubmitModal}
          moduleName={moduleName}
          year={moduleYear}
          directRecipient={directRecipient}
          moduleType={moduleType}
          uploadId={moduleUploadId}
        />
      )}
      {isRemoveConfirmationModalOpen && (
        <RemoveConfirmationModal
          onClose={closeRemoveConfirmationModal}
          moduleName={moduleName}
          year={moduleYear}
          subRecipient={null}
          moduleType={moduleType}
          moduleStatus={"Draft"}
          uploadId={moduleUploadId}
          updatedBy={updatedBy}
        />
      )}
    </div>
  );
};

export default DraftsTabTable;
