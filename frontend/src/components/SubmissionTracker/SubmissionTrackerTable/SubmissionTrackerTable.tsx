/**
 * Table containing a direct recipient's module submissions' status. Imported into the
 * Submission Tracker view.
 * @packageDocumentation
 **/
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router";

import {
  Button,
  ComboBox,
  GridContainer,
  Grid,
  Icon,
  Label,
  Pagination,
  Select,
  Tooltip,
  Table,
  ComboBoxOption,
} from "evchartstorybook";

import { OrganizationSummary } from "interfaces/Organization/organizations-interface";
import { StationInfo } from "../../../interfaces/Stations/stations-interface";
import { SortState } from "../../../interfaces/ui-components-interfaces";

import { FeatureFlagEnum, getFeatureFlagValue, getFeatureFlagList } from "../../../utils/FeatureToggle";

import {
  PATH_MODULE_SUBMISSION_TRACKER,
  PATH_REPORTING_YEARS,
  PATH_STATION_ORG_ID,
  PATH_SUB_RECIPIENTS,
} from "../../../utils/pathConstants";
import {
  ROUTE_NOT_AUTHORIZED,
  ROUTE_STATION_ID,
  ROUTE_STATION_REGISTRATION,
  ROUTE_STATION_SUBMISSION_DETAILS,
} from "../../../utils/routeConstants";

import { SubmissionTrackerIcon, SubmissionTrackerTooltip } from "./SubmissionTrackerTooltip";
import CustomLink, { CustomLinkProps } from "../../Tooltip/tooltips";

import "./SubmissionTrackerTable.css";

interface SubmissionTrackerAPIResponse {
  /**
   * The UUID that identifies a single charging station. Internal to EV-ChART database.
   */
  station_uuid: string;
  /**
   * The id that identifies a single charging station.
   */
  station_id: string;
  /**
   * The station nickname is a name created by the direct recipient to identify the
   * charging station (Station ID) more easily within EV-ChART.
   */
  nickname: string;
  /**
   * The date the station officially became operational.
   */
  operational_date: string;
  /**
   * The name of the incorporated municipality (or other general-purpose local
   * governmental unit) in which the charging station (Station ID) is located.
   */
  city: string;
  one_time: {
    module6_priority: string;
    module8_priority: string;
    module9_priority: string;
    /**
     * Rollup of module statuses for the given reporting cadence.
     *
     * Options include: "attention", "submitted", "some_submitted",
     * "not_required", "not_applicable", and "none_submitted".
     */
    hover_status: string;
  };
  annual: {
    module5_priority: string;
    module7_priority: string;
    /**
     * Rollup of module statuses for the given reporting cadence.
     *
     * Options include: "attention", "submitted", "some_submitted",
     * "not_required", "not_applicable", and "none_submitted".
     */
    hover_status: string;
  };
  quarter1: {
    module2_priority: string;
    module3_priority: string;
    module4_priority: string;
    /**
     * Rollup of module statuses for the given reporting cadence.
     *
     * Options include: "attention", "submitted", "some_submitted",
     * "not_required", "not_applicable", and "none_submitted".
     */
    hover_status: string;
  };
  quarter2: {
    module2_priority: string;
    module3_priority: string;
    module4_priority: string;
    /**
     * Rollup of module statuses for the given reporting cadence.
     *
     * Options include: "attention", "submitted", "some_submitted",
     * "not_required", "not_applicable", and "none_submitted".
     */
    hover_status: string;
  };
  quarter3: {
    module2_priority: string;
    module3_priority: string;
    module4_priority: string;
    /**
     * Rollup of module statuses for the given reporting cadence.
     *
     * Options include: "attention", "submitted", "some_submitted",
     * "not_required", "not_applicable", and "none_submitted".
     */
    hover_status: string;
  };
  quarter4: {
    module2_priority: string;
    module3_priority: string;
    module4_priority: string;
    /**
     * Rollup of module statuses for the given reporting cadence.
     *
     * Options include: "attention", "submitted", "some_submitted",
     * "not_required", "not_applicable", and "none_submitted".
     */
    hover_status: string;
  };
}

interface Submission extends SubmissionTrackerAPIResponse {
  /**
   * The name displayed in the Submission Tracker table to identify a single charging station.
   * A combination of the nickname and station_id
   */
  name: string;
}

interface SubmissionTrackerTableProps {
  /**
   * A function that, when executed, will set the state variable
   * for the Dashboard Updated timestamp to the current time.
   *
   * @returns void
   */
  updateTime: () => void;
}

export const SubmissionTrackerTable: React.FC<SubmissionTrackerTableProps> = ({ updateTime }): React.ReactElement => {
  /**
   * Set BASE_URL for the page redirects
   */
  const BASE_URL = import.meta.env.VITE_PUBLIC_URL;

  /**
   * Set API URL for API calls
   */
  const API_URL = import.meta.env.VITE_API_URL;

  /**
   * The default value for the reporting year filter.
   * Default year depends on whether today's date is before or after the April 1st reporting deadline
   */
  const today = new Date();
  const currentYear = today.getFullYear();
  const DEFAULT_VALUE_REPORTING_YEAR_FILTER = today >= new Date(currentYear, 3, 1) ?
    currentYear.toString() :
    (currentYear-1).toString();

  /**
   * State variable for the list of reporting years
   */
  const [reportingYearList, setReportingYearList] = useState<Array<string>>([]);

  /**
   * The selected reporting year from the reporting year filter.
   */
  const [selectedReportingYear, setSelectedReportingYear] = useState<string>(DEFAULT_VALUE_REPORTING_YEAR_FILTER);

  /**
   * The value of the reporting year filter after the user has clicked 'Update View'.
   *
   * This value is used as a query parameter in the API call to update the results in the table.
   */
  const [reportingYearFilter, setReportingYearFilter] = useState<string>(DEFAULT_VALUE_REPORTING_YEAR_FILTER);

  /**
   * The default value for the station filter.
   */
  const DEFAULT_VALUE_STATION_FILTER = "All";

  /**
   * State variable for the list of stations
   */
  const [stationList, setStationList] = useState<ComboBoxOption[]>([]);

  /**
   * The selected station from the station filter.
   */
  const [selectedStation, setSelectedStation] = useState<string>(DEFAULT_VALUE_STATION_FILTER);

  /**
   * The value of the station filter after the user has clicked 'Update View'.
   *
   * This value is used as a query parameter in the API call to update the results in the table.
   */
  const [stationFilter, setStationFilter] = useState<string>(DEFAULT_VALUE_STATION_FILTER);

  /**
   * The default value for the subrecipient filter.
   */
  const DEFAULT_VALUE_SUBRECIPIENT_FILTER = "All";
  const allSubrecipientsOption: ComboBoxOption = {
    value: DEFAULT_VALUE_SUBRECIPIENT_FILTER,
    label: "All Subrecipients/Contractors",
  };
  const noSubrecipientOption: ComboBoxOption = {
    value: "None",
    label: "No Subrecipients/Contractors",
  };

  /**
   * State variable for the list of subrecipients
   */
  const [subrecipientList, setSubrecipientList] = useState<ComboBoxOption[]>([]);

  /**
   * The selected subrecipient from the subrecipient filter.
   */
  const [selectedSubrecipient, setSelectedSubrecipient] = useState<string>(DEFAULT_VALUE_SUBRECIPIENT_FILTER);

  /**
   * The value of the subrecipient filter after the user has clicked 'Update View'.
   *
   * This value is used as a query parameter in the API call to update the results in the table.
   */
  const [subrecipientFilter, setSubrecipientFilter] = useState<string>(DEFAULT_VALUE_SUBRECIPIENT_FILTER);

  /**
   * State variable for the submission tracker data that will appear in the table
   */
  const [submissions, setSubmissions] = useState<Submission[]>([]);

  /**
   * Feature flag management
   * Toggles:
   *  * Station Submission Details
   *  * Subrecipient/Contractor Dropdown
   */
  const [stationSubmissionDetailsFeatureFlag, setStationSubmissionDetailsFeatureFlag] = useState<boolean>(false);
  const [submissionTrackerSubrecipientFilterFeatureFlag, setSubmissionTrackerSubrecipientFilterFeatureFlag] =
    useState<boolean>(false);

  /**
   * Validation
   */
  const initialErrorState = {
    selectedReportingYear: false,
  };
  const [formValidity, setFormValidity] = useState<{ [key: string]: boolean }>(initialErrorState);

  /**
   * Set the ID Token for API calls
   */
  const id_token = localStorage.getItem("id_token");

  /**
   * Method for changing the location / route
   */
  const navigate = useNavigate();

  useEffect(() => {
    getFeatureFlagList().then((results) => {
      setStationSubmissionDetailsFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.StationSubmissionDetails));
      setSubmissionTrackerSubrecipientFilterFeatureFlag(
        getFeatureFlagValue(results, FeatureFlagEnum.SubmissionTrackerSubrecipientFilter),
      );
    });
  }, []);

  useEffect(() => {
    /**
     * On initial render, get the list of options to populate the
     * filter dropdowns.
     *
     * Gets the list of reporting years, actives stations,
     * and subrecipients.
     */
    fetch(`${API_URL}${PATH_REPORTING_YEARS}`, {
      method: "GET",
      headers: {
        Authorization: `${id_token}`,
      },
    })
      .then((response) => response.json())
      .then((data: { year: string }[]) => {
        const reportingYearOptions: Array<string> = data
          .map((row) => row.year)
          .sort((a, b) => parseInt(b) - parseInt(a));
        setReportingYearList(reportingYearOptions);
      })
      .catch((err) => {
        console.log(err.message);
      });

    fetch(`${API_URL}${PATH_STATION_ORG_ID}?status=Active&federal_funding_status=fed_funded`, {
      method: "GET",
      headers: {
        Authorization: `${id_token}`,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        const stationSearchOptions = data.map((activeStation: StationInfo) => ({
          value: activeStation.station_uuid,
          label: `${activeStation.nickname} - ${activeStation.station_id}`,
        }));
        setStationList(stationSearchOptions);
      })
      .catch((err) => {
        const errorCode = err.status;
        if (errorCode === 401) {
          navigate(ROUTE_NOT_AUTHORIZED);
        }
        console.log(err.message);
      });

    fetch(`${API_URL}${PATH_SUB_RECIPIENTS}?only_fed_funded=true`, {
      method: "GET",
      headers: {
        Authorization: `${id_token}`,
        only_authorized: "True",
      },
    })
      .then((response) => response.json())
      .then((data) => {
        const subRecipientsList = data.map((item: OrganizationSummary) => ({
          value: item.org_id,
          label: item.name,
        }));
        subRecipientsList.unshift(allSubrecipientsOption, noSubrecipientOption);
        setSubrecipientList(subRecipientsList);
      })
      .catch((err) => {
        const errorCode = err.status;
        if (errorCode === 401) {
          navigate(ROUTE_NOT_AUTHORIZED);
        }
        console.log(err.message);
      });
  }, []);

  useEffect(() => {
    const queryParams = submissionTrackerSubrecipientFilterFeatureFlag
      ? `year=${reportingYearFilter}&station=${stationFilter}&sr_id=${subrecipientFilter}`
      : `year=${reportingYearFilter}&station=${stationFilter}`;

    /**
     * Make an API call here to get the Submission Tracker data.
     *
     * Will execute if there is a chan
     */
    fetch(`${API_URL}${PATH_MODULE_SUBMISSION_TRACKER}?${queryParams}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `${id_token}`,
      },
    })
      .then((response) => {
        if (response.ok) {
          /**
           * Handle no authorized subrecipient for filtered station
           */
          if (response.status === 204) {
            return Promise.resolve([]);
          } else {
            return response.json();
          }
        } else {
          throw response;
        }
      })
      .then((data) => {
        const mappedData = data.map((submission: SubmissionTrackerAPIResponse) => ({
          ...submission,
          name: `${submission.nickname} - ID: ${submission.station_id}`,
        }));
        setSubmissions(mappedData);
      })
      .catch((err) => {
        const errorCode = err.status;
        if (errorCode === 401) {
          navigate(ROUTE_NOT_AUTHORIZED);
        }
        console.log(err.message);
      })
      .finally(() => updateTime());
    /**
     * Re-run the GetSubmissionTracker API call when one of the filters' value changes
     * and the 'Update View' button is clicked.
     */
  }, [reportingYearFilter, stationFilter, submissionTrackerSubrecipientFilterFeatureFlag, subrecipientFilter]);

  /**
   * Manages the default sort for rows of data in the submission tracker table
   */
  const initialSortState: SortState<Submission> = {
    column: "name",
    direction: "asc",
  };
  const [sortState, setSortState] = useState(initialSortState);

  /**
   * Set the columns for the table
   */
  const columnHeaders: {
    key: keyof Submission;
    label: string;
    subLabel?: string;
  }[] = [
    { key: "name", label: "Station" },
    { key: "city", label: "Station City" },
    { key: "one_time", label: "One Time" },
    { key: "annual", label: "Annual" },
    { key: "quarter1", label: "Quarter 1", subLabel: "(Jan-Mar)" },
    { key: "quarter2", label: "Quarter 2", subLabel: "(Apr-Jun)" },
    { key: "quarter3", label: "Quarter 3", subLabel: "(Jul-Sep)" },
    { key: "quarter4", label: "Quarter 4", subLabel: "(Oct-Dec)" },
  ];

  /**
   * Change the sort state from user selection
   * @param column the selected column
   */
  const toggleSort = (column: keyof Submission) => {
    if (column === "name" || column === "city") {
      setSortState((prevState) => ({
        column,
        direction: prevState.direction === "asc" ? "desc" : "asc",
      }));
    }
  };

  /**
   * Sort data in table based on the sort state
   */
  const sortedData = [...submissions].sort((a: Submission, b: Submission) => {
    let columnA = a[sortState.column];
    let columnB = b[sortState.column];
    if (typeof columnA === "string") {
      columnA = columnA.toUpperCase();
    }
    if (typeof columnB === "string") {
      columnB = columnB.toUpperCase();
    }
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
  const RenderSortArrow = ({ column }: { column: keyof Submission }) => {
    if (column === "name" || column === "city") {
      if (column === sortState.column) {
        if (sortState.direction === "asc") {
          return <Icon.ArrowUpward className="sort-icon" />;
        } else {
          return <Icon.ArrowDownward className="sort-icon" />;
        }
      }
      return <Icon.SortArrow className="sort-icon" />;
    } else return <></>;
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
   * Handle user selecting a value from the reporting year filer
   */
  const updateReportingYear = (value: string) => {
    setFormValidity(() => ({
      selectedReportingYear: false,
    }));

    setSelectedReportingYear(value);
  };

  /**
   * Handle user selecting a value from the subrecipient filer
   */
  const handleSubrecipientChange = (value?: string) => {
    setSelectedSubrecipient(value === undefined ? allSubrecipientsOption.value : value);
  };

  /**
   * Update state variables to trigger back-end filtering
   */
  const updateSubmissionTrackerData = () => {
    if (selectedReportingYear === "") {
      setFormValidity({
        selectedReportingYear: true,
      });
    } else {
      setStationFilter(selectedStation);
      setReportingYearFilter(selectedReportingYear);
      setSubrecipientFilter(selectedSubrecipient);
    }
  };

  function inputValid(field: boolean, type: string): string {
    if (field && type === "combobox") {
      return "error-combobox";
    } else if (field) {
      return "usa-input--error";
    } else {
      return "";
    }
  }

  return (
    <div className="submission-tracker-table-container">
      <Grid row gap={3} className="submission-tracker-filters">
        <Grid col="auto">
          {reportingYearList.length > 0 && (
            <>
              <div className="label-tooltip-container">
                <Label htmlFor="selectedReportingYear" className="required-field">
                  Reporting Year
                </Label>
                <Tooltip label="The reporting year associated with the submitted module data" asCustom={CustomLink}>
                  <Icon.InfoOutline className="tooltip-icon tooltip-icon--margin-left-05" />
                </Tooltip>
              </div>
              <Select
                id="selectedReportingYear"
                name="selectedReportingYear"
                value={selectedReportingYear}
                className={inputValid(formValidity.selectedReportingYear, "field")}
                onChange={(e) => updateReportingYear(e.target.value)}
              >
                {reportingYearList.map((year, index) => {
                  return (
                    <option key={index} value={year}>
                      {year}
                    </option>
                  );
                })}
              </Select>
            </>
          )}
        </Grid>
        <Grid col={4}>
          {stationList.length !== 0 && (
            <>
              <Label htmlFor="stationSearch">Search by Station</Label>
              <ComboBox
                id="stationSearch"
                name="stationSearch"
                options={stationList}
                onChange={(e) => {
                  setSelectedStation(e === undefined ? DEFAULT_VALUE_STATION_FILTER : e);
                }}
                inputProps={{ placeholder: "Station ID or Station Nickname" }}
              />
            </>
          )}
        </Grid>
        {submissionTrackerSubrecipientFilterFeatureFlag && (
          <Grid col="auto">
            {subrecipientList.length > 0 && (
              <>
                <Label htmlFor="input-subrecipient">Search by Subrecipient/Contractor</Label>
                <ComboBox
                  id={`input-subrecipient`}
                  name={`input-subrecipient`}
                  options={subrecipientList}
                  defaultValue={allSubrecipientsOption.value}
                  onChange={handleSubrecipientChange}
                />
              </>
            )}
          </Grid>
        )}
        <Grid col>
          <Button
            type="button"
            className="submission-tracker__update-view-button"
            onClick={updateSubmissionTrackerData}
          >
            Update View
          </Button>
        </Grid>
      </Grid>
      <h2 className="submission-tracker__subheading">Station Module Submissions</h2>
      <div id="SubmissionTrackerTable" className="submission-tracker-table" data-testid="SubmissionTrackerTable">
        <Grid row className="pagination-info-row-container">
          <div className="pagination-info-row">
            {sortedData.length > 10 && (
              <>
                <p className="pagination-info-row-count">
                  {startIndex + 1}-{endIndex > totalItems ? totalItems : endIndex} of {totalItems} rows
                </p>
                <p className="pagination-info-row-per-page">Rows per page:</p>
                <Select
                  id="usersSelectItemsPerPage"
                  name="users-select-items-per-page"
                  title="users-select-items-per-page"
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
        </Grid>
        <Table striped fullWidth bordered={false}>
          <thead>
            <tr>
              {columnHeaders.map(({ key, label, subLabel }) => (
                <th className={`submission-tracker-table__th ${key}`} key={key} scope="col" data-testid={key}>
                  <div className={key + "ColumnHeader columnHeader"} onClick={() => toggleSort(key)}>
                    <span>
                      <div>
                        <div className="quarterLabel">
                          {key === "one_time" ? (
                            <span className="submission-tracker-table__header-tooltip">
                              {label}
                              <Tooltip
                                label="Tracking for One Time submissions will roll over from year-to-year."
                                asCustom={CustomLink}
                              >
                                <Icon.InfoOutline className="tooltip-icon tooltip-icon--margin-left-05 tooltip-icon--table-header" />
                              </Tooltip>
                            </span>
                          ) : (
                            <>{label}</>
                          )}
                        </div>
                        <div className="quarterSubLabel">{subLabel}</div>
                      </div>
                    </span>
                    <span>
                      <RenderSortArrow column={key} />
                    </span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          {submissions.length === 0 ? (
            <tbody data-testid="noDataAddStationSubmission">
              <tr>
                <td colSpan={columnHeaders.length + 1}>
                  <Grid col={12} className="no-data-add-station-submission" style={{}}>
                    <p>
                      {stationFilter === DEFAULT_VALUE_STATION_FILTER &&
                      subrecipientFilter === DEFAULT_VALUE_SUBRECIPIENT_FILTER ? (
                        <>
                          <a className="evchart-link" href={`${BASE_URL}${ROUTE_STATION_REGISTRATION}`}>
                            Add a station
                          </a>{" "}
                          to start tracking submission progress.
                        </>
                      ) : (
                        <>There is no data to match your selected filters</>
                      )}
                    </p>
                  </Grid>
                </td>
              </tr>
            </tbody>
          ) : (
            <tbody data-testid="submissionData">
              {visibleData.map((item, index) => (
                <tr data-testid="submissionRow" key={index}>
                  <td className="submission-tracker-table__td">
                    <Button
                      type="button"
                      className="evchart-button-link"
                      unstyled
                      onClick={() =>
                        stationSubmissionDetailsFeatureFlag
                          ? navigate(`${ROUTE_STATION_SUBMISSION_DETAILS}/${item.station_uuid}`, {
                              state: {
                                year: reportingYearFilter,
                              },
                            })
                          : navigate(`${ROUTE_STATION_ID}/${item.station_uuid}`)
                      }
                    >
                      {item.name}
                    </Button>
                  </td>
                  <td className="submission-tracker-table__td submission-tracker-table__td--city">
                    <div className="overflow-ellipsis overflow-ellipsis--two-lines">{item.city}</div>
                  </td>
                  <td className="submission-tracker-table__td submission-tracker-table__td--status submission-tracker-table__td--one-time">
                    <Tooltip<CustomLinkProps>
                      position="bottom"
                      label={
                        <SubmissionTrackerTooltip
                          data={item.one_time}
                          reportingPeriod="one_time"
                          reportingYear={reportingYearFilter}
                        />
                      }
                      asCustom={CustomLink}
                      wrapperclasses="submission-tracker-tooltip-container"
                    >
                      <SubmissionTrackerIcon hoverStatus={item.one_time.hover_status} />
                    </Tooltip>
                  </td>
                  <td className="submission-tracker-table__td submission-tracker-table__td--status submission-tracker-table__td--annual">
                    <Tooltip<CustomLinkProps>
                      position="bottom"
                      label={
                        <SubmissionTrackerTooltip
                          data={item.annual}
                          reportingPeriod="annual"
                          reportingYear={reportingYearFilter}
                        />
                      }
                      asCustom={CustomLink}
                      wrapperclasses="submission-tracker-tooltip-container"
                    >
                      <SubmissionTrackerIcon hoverStatus={item.annual.hover_status} />
                    </Tooltip>
                  </td>
                  <td className="submission-tracker-table__td submission-tracker-table__td--status">
                    <Tooltip<CustomLinkProps>
                      position="bottom"
                      label={
                        <SubmissionTrackerTooltip
                          data={item.quarter1}
                          reportingPeriod="quarter1"
                          reportingYear={reportingYearFilter}
                        />
                      }
                      asCustom={CustomLink}
                      wrapperclasses="submission-tracker-tooltip-container"
                    >
                      <SubmissionTrackerIcon hoverStatus={item.quarter1.hover_status} />
                    </Tooltip>
                  </td>
                  <td className="submission-tracker-table__td submission-tracker-table__td--status">
                    <Tooltip<CustomLinkProps>
                      position="bottom"
                      label={
                        <SubmissionTrackerTooltip
                          data={item.quarter2}
                          reportingPeriod="quarter2"
                          reportingYear={reportingYearFilter}
                        />
                      }
                      asCustom={CustomLink}
                      wrapperclasses="submission-tracker-tooltip-container"
                    >
                      <SubmissionTrackerIcon hoverStatus={item.quarter2.hover_status} />
                    </Tooltip>
                  </td>
                  <td className="submission-tracker-table__td submission-tracker-table__td--status">
                    <Tooltip<CustomLinkProps>
                      position="bottom"
                      label={
                        <SubmissionTrackerTooltip
                          data={item.quarter3}
                          reportingPeriod="quarter3"
                          reportingYear={reportingYearFilter}
                        />
                      }
                      asCustom={CustomLink}
                      wrapperclasses="submission-tracker-tooltip-container"
                    >
                      <SubmissionTrackerIcon hoverStatus={item.quarter3.hover_status} />
                    </Tooltip>
                  </td>
                  <td className="submission-tracker-table__td submission-tracker-table__td--status">
                    <Tooltip<CustomLinkProps>
                      position="bottom"
                      label={
                        <SubmissionTrackerTooltip
                          data={item.quarter4}
                          reportingPeriod="quarter4"
                          reportingYear={reportingYearFilter}
                        />
                      }
                      asCustom={CustomLink}
                      wrapperclasses="submission-tracker-tooltip-container"
                    >
                      <SubmissionTrackerIcon hoverStatus={item.quarter4.hover_status} />
                    </Tooltip>
                  </td>
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
                  pathname="management/track-submissions"
                  currentPage={current}
                  onClickNext={handleNext}
                  onClickPrevious={handlePrevious}
                  onClickPageNumber={handlePageNumber}
                />
              </div>
            </Grid>
          </GridContainer>
        )}
      </div>
    </div>
  );
};

export default SubmissionTrackerTable;
