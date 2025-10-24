/**
 * Dropdown filters for the Program Performance Dashboard.
 * @packageDocumentation
 **/
import React, { createRef, Dispatch, ReactElement, SetStateAction, useEffect, useState } from "react";

import {
  Button,
  ComboBox,
  ComboBoxOption,
  ComboBoxRef,
  Grid,
  Icon,
  Label,
  Select,
  SelectOpt,
  Tooltip,
} from "evchartstorybook";

import CustomLink from "../../components/Tooltip/tooltips";
import { OrganizationSummary, OrgNameAndIDType } from "../../interfaces/Organization/organizations-interface";
import { StationInfo } from "../../interfaces/Stations/stations-interface";

import { isDRUser, isJOUser } from "../../utils/authFunctions";
import { FeatureFlagEnum, getFeatureFlagValue, getFeatureFlagList } from "../../utils/FeatureToggle";
import {
  PATH_DIRECT_RECIPIENTS,
  PATH_STATION_ORG_ID,
  PATH_SUB_RECIPIENTS,
  PATH_REPORTING_YEARS,
} from "../../utils/pathConstants";

interface SelectOptOptions {
  value: string;
  label: string;
}

interface ProgramPerformanceDashboardFiltersProps {
  /**
   * The state variable for the value of the DR filter
   */
  drFilter: string;
  /**
   * The set function for the DR filter
   */
  setDRFilter: Dispatch<SetStateAction<string>>;
  /**
   * The state variable for the value of the station filter
   */
  stationFilter: string;
  /**
   * The set function for the station filter
   */
  setStationFilter: Dispatch<SetStateAction<string>>;
  /**
   * The state variable for the value of the subrecipient filter
   */
  subrecipientFilter: string;
  /**
   * The set function for the subrecipient filter
   */
  setSubrecipientFilter: Dispatch<SetStateAction<string>>;
  /**
   * The state variable for the value of the reporting year filter
   */
  reportingYearFilter: string;
  /**
   * The set function for the reporting year filter
   */
  setReportingYearFilter: Dispatch<SetStateAction<string>>;
  /**
   * The Option displayed in the reporting year filter to indicate all reporting years
   */
  allReportingYearsOption: { value: string; label: string };
  /**
   * The state variable for whether the Update View button is disabled
   */
  updateViewDisabled: boolean;
  /**
   * The set function for the updateViewDisabled state variable
   */
  setUpdateViewDisabled: Dispatch<SetStateAction<boolean>>;
}

const ProgramPerformanceDashboardFilters: React.FC<ProgramPerformanceDashboardFiltersProps> = ({
  drFilter,
  setDRFilter,
  stationFilter,
  setStationFilter,
  subrecipientFilter,
  setSubrecipientFilter,
  reportingYearFilter,
  setReportingYearFilter,
  allReportingYearsOption,
  updateViewDisabled,
  setUpdateViewDisabled,
}): ReactElement => {
  /**
   * Set API URL for API calls
   */
  const API_URL = import.meta.env.VITE_API_URL;

  /**
   * Set the ID Token for API calls
   */
  const id_token = localStorage.getItem("id_token");

  /**
   * Set the options from API for direct recipient select
   */
  const [directRecipients, setDirectRecipients] = useState<SelectOptOptions[]>([
    {
      value: "",
      label: "",
    },
  ]);

  const refStationComboBox = createRef<ComboBoxRef>();

  /**
   * The Option displayed in the station filter to indicate all stations.
   */
  const defaultStation: ComboBoxOption = {
    value: "All",
    label: "All Stations",
  };

  /**
   * State variable for the list of stations.
   */
  const [stations, setStations] = useState<ComboBoxOption[]>([]);

  const refSubrecipientComboBox = createRef<ComboBoxRef>();

  /**
   * The Option displayed in the subrecipient filter to indicate all
   * subrecipients and contractors.
   */
  const defaultSubrecipient: ComboBoxOption = {
    value: "All",
    label: "All Subrecipients/Contractors",
  };
  const noSubrecipientOption: ComboBoxOption = {
    value: "None",
    label: "No Subrecipients/Contractors",
  };

  /**
   * State variable for the list of subrecipients.
   */
  const [subrecipients, setSubrecipients] = useState<ComboBoxOption[]>([]);

  /**
   * State variable for the list of reporting years.
   */
  const [reportingYears, setReportingYears] = useState<SelectOptOptions[]>([]);

  /**
   * State variables to store the currently selected values from the filters.
   */
  const [selectedDR, setSelectedDR] = useState<string>("All");
  const [selectedStation, setSelectedStation] = useState<string>("All");
  const [selectedSubrecipient, setSelectedSubrecipient] = useState<string>("All");
  const [selectedReportingYear, setSelectedReportingYear] = useState<string>(allReportingYearsOption.value);

  /**
   * Feature flag management
   * Toggles the Reporting Year Dropdown
   */
  const [drPPDashboardReportingYearFeatureFlag, setDrPPDashboardReportingYearFeatureFlag] = useState(false);

  const [showFilters, setShowFilters] = useState<boolean>();

  useEffect(() => {
    /**
     * On initial render, get the feature flag list and, using its results,
     * set the drPPDashboardReportingYearFeatureFlag state variable.
     */
    getFeatureFlagList().then((results) => {
      setDrPPDashboardReportingYearFeatureFlag(
        getFeatureFlagValue(results, FeatureFlagEnum.DRPPDashboardReportingYear),
      );
    });
  }, []);

  useEffect(() => {
    /**
     * On initial render, get the list of options to populate the
     * filter dropdowns.
     *
     * Dependent on the user.
     *
     * If JO user, get the list of Direct Recipients.
     *
     * If DR user, get the list of actives stations, subrecipients,
     * and reporting years.
     */
    if (isJOUser()) {
      fetch(`${API_URL}${PATH_DIRECT_RECIPIENTS}`, {
        method: "GET",
        headers: {
          Authorization: `${id_token}`,
        },
      })
        .then((response) => response.json())
        .then((data) => {
          const drList: SelectOptOptions[] = [
            {
              value: "",
              label: "All Direct Recipients",
            },
          ];
          data.forEach((dr: OrgNameAndIDType) => {
            drList.push({
              value: dr["org_id"],
              label: dr["name"],
            });
          });
          setDirectRecipients(drList);
        })
        .catch((err) => {
          console.log(err.message);
        });
    } else {
      fetch(`${API_URL}${PATH_STATION_ORG_ID}?status=Active&federal_funding_status=fed_funded`, {
        method: "GET",
        headers: {
          Authorization: `${id_token}`,
        },
      })
        .then((response) => response.json())
        .then((data) => {
          const stationsList = data.map((item: StationInfo) => ({
            value: item.station_uuid,
            label: `${item.nickname} - ${item.station_id}`,
          }));
          stationsList.unshift(defaultStation);
          setStations(stationsList);
        })
        .catch((err) => {
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
          subRecipientsList.unshift(defaultSubrecipient, noSubrecipientOption);
          setSubrecipients(subRecipientsList);
        })
        .catch((err) => {
          console.log(err.message);
        });

      fetch(`${API_URL}${PATH_REPORTING_YEARS}`, {
        method: "GET",
        headers: {
          Authorization: `${id_token}`,
        },
      })
        .then((response) => response.json())
        .then((data: { year: string }[]) => {
          const reportingYearOptions: SelectOptOptions[] = data
            .map((row) => ({
              value: row.year,
              label: row.year,
            }))
            .sort((a, b) => parseInt(b.value) - parseInt(a.value));
          reportingYearOptions.unshift(allReportingYearsOption);
          setReportingYears(reportingYearOptions);
        })
        .catch((err) => {
          console.log(err.message);
        });
    }
  }, []);

  /**
   * A function called when the user selects an option from the DR filter.
   *
   * @param e ChangeEvent for the SelectOpt component
   */
  const handleDRChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedDR(e.target.value === "" ? "All" : e.target.value);
    setUpdateViewDisabled(false);
  };

  /**
   * A function called when the user selects a option from the station filter.
   *
   * @param value The station_uuid of the station selected
   */
  const handleStationChange = (value?: string) => {
    if (value !== selectedStation) {
      setUpdateViewDisabled(false);
    }
    setSelectedStation(value === undefined ? "All" : value);
  };

  /**
   * A function called when the user selects a option from the subrecipient filter.
   *
   * @param value The org_id of the subrecipient selected
   */
  const handleSubrecipientChange = (value?: string) => {
    if (value !== selectedSubrecipient) {
      setUpdateViewDisabled(false);
    }
    setSelectedSubrecipient(value === undefined ? "All" : value);
  };

  /**
   * A function called when the user selects a option from the reporting year filter.
   *
   * @param value The reporting year selected
   */
  const handleReportingYearChange = (value: string) => {
    if (value !== selectedReportingYear) {
      setUpdateViewDisabled(false);
    }

    setSelectedReportingYear(value);
  };

  /**
   * A function called when the 'Update View' button is clicked.
   *
   * Sets the state variables for the filter values.
   */
  const updateDashboardView = () => {
    if (isJOUser()) {
      setDRFilter(selectedDR);
    } else {
      setStationFilter(selectedStation);
      setSubrecipientFilter(selectedSubrecipient);
      setReportingYearFilter(selectedReportingYear);
    }
    setUpdateViewDisabled(true);
  };

  /**
   * A function called when the 'Cancel' button is clicked.
   *
   * Reverts filter changes and disable 'Update View' button.
   */
  const handleCancel = () => {
    if (isJOUser()) {
      setSelectedDR(drFilter);
    } else {
      setSelectedStation(stationFilter);

      // set value of station combobox
      const stationFilterOption = stations.find((station) => station.value === stationFilter);
      if (stationFilterOption) {
        refStationComboBox.current?.selectOption(stationFilterOption);
      }

      setSelectedSubrecipient(subrecipientFilter);

      // set value of subrecipient combobox
      const subrecipientFilterOption = subrecipients.find((subrecipient) => subrecipient.value === subrecipientFilter);
      if (subrecipientFilterOption) {
        refSubrecipientComboBox.current?.selectOption(subrecipientFilterOption);
      }

      setSelectedReportingYear(reportingYearFilter);
    }
    setUpdateViewDisabled(true);
  };

  useEffect(() => {
    /**
     * When the state variables for the filter options change,
     * checks if the options have length greater than 0.
     */
    if (isJOUser()) {
      setShowFilters(true);
    } else {
      const showDRFilters = stations.length > 0 || subrecipients.length > 0 || reportingYears.length > 0;
      setShowFilters(showDRFilters);
    }
  }, [directRecipients, stations, subrecipients, reportingYears]);

  return (
    <Grid row gap className="pp-dashboard-filter-container">
      {showFilters && (
        <>
          {isJOUser() ? (
            <>
              <Grid col={4}>
                <Label htmlFor="directRecipient">Select Direct Recipient:</Label>
                <SelectOpt
                  id="directRecipient"
                  name="directRecipient"
                  options={directRecipients}
                  value={selectedDR}
                  onChange={handleDRChange}
                >
                  <option value="All">All Direct Recipients</option>
                </SelectOpt>
              </Grid>
            </>
          ) : (
            <>
              {drPPDashboardReportingYearFeatureFlag && (
                <Grid col="auto">
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
                    onChange={(e) => handleReportingYearChange(e.target.value)}
                  >
                    {reportingYears.map((reportingYearOption, index) => {
                      return (
                        <option key={index} value={reportingYearOption.value}>
                          {reportingYearOption.label}
                        </option>
                      );
                    })}
                  </Select>
                </Grid>
              )}
              <Grid col={4}>
                {stations.length > 0 && (
                  <>
                    <Label htmlFor="input-station">Search by Station</Label>
                    <ComboBox
                      id={`input-station`}
                      name={`input-station`}
                      options={stations}
                      defaultValue={defaultStation.value}
                      onChange={handleStationChange}
                      ref={refStationComboBox}
                    />
                  </>
                )}
              </Grid>
              <Grid col="auto">
                {subrecipients.length > 0 && (
                  <>
                    <Label htmlFor="input-subrecipient">Search by Subrecipient/Contractor</Label>
                    <ComboBox
                      id={`input-subrecipient`}
                      name={`input-subrecipient`}
                      options={subrecipients}
                      defaultValue={defaultSubrecipient.value}
                      onChange={handleSubrecipientChange}
                      ref={refSubrecipientComboBox}
                    />
                  </>
                )}
              </Grid>
            </>
          )}
          <Grid
            col="auto"
            className={`update-view-button-container ${isDRUser() && drPPDashboardReportingYearFeatureFlag ? "update-view-button-container--new-row" : ""}`}
          >
            <Button
              type="button"
              outline
              disabled={updateViewDisabled}
              className="padding-x-2"
              onClick={() => updateDashboardView()}
            >
              Update View
            </Button>
            {!updateViewDisabled && (
              <Button type="button" unstyled className="padding-left-2 text-center" onClick={handleCancel}>
                Cancel
              </Button>
            )}
          </Grid>
        </>
      )}
    </Grid>
  );
};

export default ProgramPerformanceDashboardFilters;
