/**
 * Table containing a summary of all of the stations. Imported into the Stations view.
 * @packageDocumentation
 **/
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router";

import { Actions, Button, Icon, Grid, GridContainer, Pagination, Select, Table, Spinner, Chip } from "evchartstorybook";

import { StationInfo } from "../../interfaces/Stations/stations-interface";
import { SortState } from "../../interfaces/ui-components-interfaces";

import { isAdmin, isJOUser } from "../../utils/authFunctions";
import { FeatureFlagEnum, getFeatureFlagValue, getFeatureFlagList } from "../../utils/FeatureToggle";
import { getScope } from "../../utils/getJWTInfo";
import { PATH_STATION_ORG_ID } from "../../utils/pathConstants";
import {
  ROUTE_AUTHROIZE_CONTRACTORS,
  ROUTE_EDIT,
  ROUTE_STATION_ID,
  ROUTE_STATION_REGISTRATION,
} from "../../utils/routeConstants";

import "./StationSummary.css";

/**
 * Interface defining the props that are passed to the StationSummary component
 */
interface StationSummaryProps {
  /**
   * Function to open the column definitions modal
   */
  setColumnDefinitionsModal: () => void;
  /**
   * Function to open the remove station modal
   */
  setRemoveStationModal: () => void;
  /**
   * Function to remove a station/ open the remove modal
   * @param station the info for station selected for removal
   */
  setStationToRemove: (station: StationInfo) => void;
}

export const StationSummary: React.FC<StationSummaryProps> = ({
  setColumnDefinitionsModal,
  setRemoveStationModal,
  setStationToRemove,
}): React.ReactElement => {
  /**
   * Set BASE_URL for the page redirects
   */
  const BASE_URL = import.meta.env.VITE_PUBLIC_URL;
  /**
   * Get the api url from the environment variables
   */
  const API_URL = import.meta.env.VITE_API_URL;

  /**
   * Org variables
   */
  const recipientType = getScope();

  const navigate = useNavigate();

  /**
   * State variable for the list of stations.
   */
  const [stations, setStations] = useState<StationInfo[]>([]);

  /**
   * Feature flag management
   * Toggles:
   *  * Remove Station action
   *  * Authorize Contractors action
   *  * Toggle on federally funded status
   */
  const [removeStationFeatureFlag, setRemoveStationFeatureFlag] = useState(false);
  const [nTierFeatureFlag, setNTierFeatureFlag] = useState(false);
  const [registerNonFedFundedStationFeatureFlag, setRegisterNonFedFundedStationFeatureFlag] = useState(false);

  /**
   * State variable to check if get stations API call is still executing.
   */
  const [isDataLoading, setIsDataLoading] = useState(true);

  useEffect(() => {
    /**
     * On initial render, get the feature flag list and, using its results,
     * set the feature flag state variables.
     */
    getFeatureFlagList().then((results) => {
      setRemoveStationFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.RemoveStation));
      setNTierFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.NTierOrganizations));
      setRegisterNonFedFundedStationFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.RegisterNonFedFundedStation));
    });
  }, []);

  /**
   * Handle viewing station details
   * Redirects user to the station details view
   * @param id the uuid of the station that the user has selected
   * @returns button to be rendered in the actions dropdown
   */
  const ViewDetails = (id: string) => {
    return (
      <Button type="button" onClick={() => navigate(`${ROUTE_STATION_ID}/${id}`)}>
        View Details
      </Button>
    );
  };

  /**
   * Handle reviewing station details
   * Redirects user to the station details view
   * @param id the uuid of the station that the user has selected
   * @returns button to be rendered in the actions dropdown
   */
  const ReviewStationDetails = (id: string) => {
    return (
      <Button type="button" id="review-station-details-button" onClick={() => navigate(`${ROUTE_STATION_ID}/${id}`)}>
        Review Station Details
      </Button>
    );
  };

  /**
   * Handle editing station details
   * Redirects user to the edit route of the station details view
   * @param id the uuid of the station that the user has selected
   * @returns button to be rendered in the actions dropdown
   */
  const Edit = (id: string) => {
    return (
      <Button type="button" onClick={() => navigate(`${ROUTE_STATION_ID}/${id}${ROUTE_EDIT}`)}>
        Edit
      </Button>
    );
  };

  /**
   * Handle user authorize contractors a given station
   * Redirects user to the authorize contractor route on the station details view
   * @param id the uuid of the station that the user has selected
   * @returns button to be rendered in the actions dropdown
   */
  const AuthorizeContractors = (id: string) => {
    return (
      <Button type="button" onClick={() => navigate(`${ROUTE_STATION_ID}/${id}${ROUTE_AUTHROIZE_CONTRACTORS}`)}>
        Authorize Contractors
      </Button>
    );
  };

  /**
   * Get access token for endpoint authorization
   */
  const id_token = localStorage.getItem("id_token");

  useEffect(() => {
    fetch(`${API_URL}${PATH_STATION_ORG_ID}/`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `${id_token}`,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        setStations(data);
      })
      .catch((err) => {
        console.log(err.message);
      })
      .finally(() => setIsDataLoading(false));
  }, [setRemoveStationModal]);

  /**
   * Manages the default sort for rows of data in the station summary table
   */
  const initialSortState: SortState<StationInfo> = {
    column: "status",
    direction: "desc",
  };
  const [sortState, setSortState] = useState(initialSortState);

  /**
   * Set the columns for the table
   */
  const columnHeaders: { key: keyof StationInfo; label: string }[] = [
    { key: "nickname", label: "Station Nickname" },
    { key: "station_id", label: "Station ID" },
  ];
  if (recipientType === "direct-recipient") {
    columnHeaders.push({ key: "status", label: "Status" });
    columnHeaders.push({ key: "authorized_subrecipients", label: "Subrecipient/Contractor" });
  } else if (recipientType === "sub-recipient") {
    columnHeaders.push({ key: "status", label: "Status" });
    columnHeaders.push({ key: "dr_name", label: "Direct Recipient" });
  } else if (recipientType === "joet") {
    columnHeaders.push({ key: "dr_name", label: "Direct Recipient" });
  }
  if (registerNonFedFundedStationFeatureFlag) {
    columnHeaders.push({ key: "federally_funded", label: "Federally Funded"});
  }
  /**
   * Change the sort state from user selection
   * @param column the selected column
   */
  const toggleSort = (column: keyof StationInfo) => {
    if (
      column === "nickname" ||
      column === "station_id" ||
      column === "dr_name" ||
      column === "authorized_subrecipients" ||
      column === "status" ||
      (column === "federally_funded" && registerNonFedFundedStationFeatureFlag)
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
  const sortedData = [...stations].sort((a: StationInfo, b: StationInfo) => {
    const columnA = a[sortState.column]?.toString().toUpperCase();
    const columnB = b[sortState.column]?.toString().toUpperCase();
    const direction = sortState.direction === "asc" ? 1 : -1;
    if (columnA < columnB) return -direction;
    if (columnA > columnB) return direction;
    return 0;
  });

  /**
   * Function to determine which arrow (up, down, double) to render based on current sort state
   * @param column the label for the column being checked
   * @returns the appropriate arrow based on current sort state
   */
  const renderSortArrow = (column: string) => {
    if (
      column === "nickname" ||
      column === "station_id" ||
      column === "dr_name" ||
      column === "authorized_subrecipients" ||
      column === "status" ||
      (column === "federally_funded" && registerNonFedFundedStationFeatureFlag)
    ) {
      if (column === sortState.column) {
        if (sortState.direction === "asc") {
          return <Icon.ArrowUpward className="sort-icon" />;
        } else {
          return <Icon.ArrowDownward className="sort-icon" />;
        }
      }
      return <Icon.SortArrow className="sort-icon" />;
    }
  };

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
   * Function to display either the authorized subrecipients or the direct recipient name
   * in the table based on the user
   * @param item the station information from the current row
   * @returns authorized subrecipient or direct recipient name
   */
  function getAuthorizedOrDirectRecipient(item: any) {
    if (recipientType === "direct-recipient") {
      return item.authorized_subrecipients;
    } else if (recipientType === "sub-recipient" || recipientType === "joet") {
      return item.dr_name;
    }
  }

  /**
   * Function to open the remove station modal
   * @param stationToRemove information about the row/station the user selected
   */
  const openRemoveStationModal = (stationToRemove: StationInfo) => {
    setStationToRemove(stationToRemove);
    setRemoveStationModal();
  };

   /**
   * Handle removing station
   * Opens the modal to remove a station
   * @param stationToRemove information about the row/station the user selected
   * @returns button to be rendered in the actions dropdown
   */
  const RemoveStation = (stationToRemove: StationInfo) => {
    return (
      <Button type="button" onClick={() => openRemoveStationModal(stationToRemove)}>
        Remove Station
      </Button>
    );
  };

  /**
   * Function to get the appropriate icon based on status
   * @param status the status of the station (Active, Pending Approval)
   * @returns the styled chip
   */
  const getIcon = (status: string) => {
    let moduleChip: React.ReactElement;
    switch (status) {
      case "Active":
      default:
        moduleChip = <Chip type="success">Active</Chip>;
        break;
      case "Pending Approval":
        moduleChip =(
          <Chip type="warning">
            Pending
            <br />
            Approval
          </Chip>
        );
        break;
    }
    return moduleChip;
  };

  /**
   * Get the available actions for a row/station in the table
   * @param item the station information from the current row
   * @returns the set of actions available to users
   */
  function getActions(item: any) {
    let actions = [];
    if (recipientType === "direct-recipient" && isAdmin()) {
      if (item.status === "Pending Approval") {
        actions = [
          {
            name: "Review Station Details",
            component: ReviewStationDetails(item.station_uuid),
          },
        ];
      } else {
        actions = [
          {
            name: "Edit",
            component: Edit(item.station_uuid),
          },
          {
            name: "View Details",
            component: ViewDetails(item.station_uuid),
          },
        ];
        if (removeStationFeatureFlag && item.removable) {
          actions.push({
            name: "RemoveStation",
            component: RemoveStation(item),
          });
        }
      }
    } else if (nTierFeatureFlag) {
      actions = [
        {
          name: "Authorize Contractors",
          component: AuthorizeContractors(item.station_uuid),
        },
        {
          name: "View Details",
          component: ViewDetails(item.station_uuid),
        },
      ];
    } else {
      return (
        <a href={`${BASE_URL}${ROUTE_STATION_ID}/${item.station_uuid}`} className="evchart-link">
          View Details
        </a>
      );
    }
    return (
      <Actions
        item={{
          options: actions,
        }}
      />
    );
  }

  return (
    <div id="SummaryTableStations" className="summary-table-stations" data-testid="SummaryTableStations">
      {isDataLoading ? (
        <div className="pp-dashboard-spinner-container">
          <div className="pp-dashboard-spinner">
            <Spinner />
          </div>
        </div>
      ) : (
        <>
          <GridContainer className="station-pagination-info">
            <Grid row className="pagination-info-row-container">
              <div className="pagination-info-row">
                {sortedData.length > 10 && (
                  <>
                    <p className="pagination-info-row-count">
                      {startIndex + 1}-{endIndex > totalItems ? totalItems : endIndex} of {totalItems} rows
                    </p>
                    <p className="pagination-info-row-per-page">Rows per page:</p>
                    <Select
                      id="stationsSelectItemsPerPage"
                      name="stations-select-items-per-page"
                      title="stations-select-items-per-page"
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
          <Table striped fullWidth bordered={false}>
            <thead>
              <tr>
                {columnHeaders.map(({ key, label }) => (
                  <th key={key} scope="col" data-testid={key}>
                    <div className="columnHeader" onClick={() => toggleSort(key)}>
                      <span>{label}</span>
                      <span>{renderSortArrow(key)}</span>
                    </div>
                  </th>
                ))}
                <th>Actions</th>
              </tr>
            </thead>
            {stations.length === 0 && isAdmin() ? (
              <tbody data-testid="noDataAddStation">
                <tr>
                  <td colSpan={columnHeaders.length + 1}>
                    <Grid col={12} className="no-data-add-station" style={{}}>
                      {recipientType === "direct-recipient" ? (
                        <p>
                          <a className="evchart-link" href={`${BASE_URL}${ROUTE_STATION_REGISTRATION}`}>
                            Add a station
                          </a>{" "}
                          to get started
                        </p>
                      ) : (
                        <p>You have not been authorized to upload data for any station.</p>
                      )}
                    </Grid>
                  </td>
                </tr>
              </tbody>
            ) : (
              <tbody data-testid="stationData">
                {visibleData.map((item, index) => (
                  <tr className="station-row" data-testid="stationRow" key={index}>
                    <th scope="row" className="station_nickname overflow-ellipsis">
                      <a className="evchart-link" href={`${BASE_URL}${ROUTE_STATION_ID}/${item.station_uuid}`}>
                        {item.nickname}{" "}
                      </a>
                    </th>
                    <td className="station_id overflow-ellipsis">{item.station_id}</td>
                    {!isJOUser() && <td className="station_id overflow-ellipsis">{getIcon(item.status)}</td>}
                    <td className="station_authorized overflow-ellipsis">{getAuthorizedOrDirectRecipient(item)}</td>
                    {registerNonFedFundedStationFeatureFlag &&
                      <td className="station_federally_funded overflow-ellipsis"> {item.federally_funded ? "Yes" : "No"}</td>
                    }
                    <td>{getActions(item)}</td>
                  </tr>
                ))}
              </tbody>
            )}
          </Table>
          {sortedData.length > 10 && (
            <GridContainer>
              <Grid row style={{ justifyContent: "center" }}>
                <div>
                  <Pagination
                    totalPages={numberOfPages}
                    pathname="management/stations"
                    currentPage={current}
                    onClickNext={handleNext}
                    onClickPrevious={handlePrevious}
                    onClickPageNumber={handlePageNumber}
                  />
                </div>
              </Grid>
            </GridContainer>
          )}
        </>
      )}
    </div>
  );
};

export default StationSummary;
