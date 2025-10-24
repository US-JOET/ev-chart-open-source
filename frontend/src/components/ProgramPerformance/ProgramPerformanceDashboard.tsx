/**
 * Dashboard component showing program performance metrics. Imported into the
 * Joint Office and Direct Recipient home pages.
 * @packageDocumentation
 **/
import { Dispatch, ReactElement, SetStateAction, useEffect, useState } from "react";

import { useNavigate } from "react-router-dom";

import { Alert, Button, Grid, GridContainer, Icon, Spinner, Tooltip } from "evchartstorybook";

import {
  CapitalCostsInterface,
  EnergyUsageInterface,
  NetworkSizeInterface,
  ReliabilityInterface,
} from "./../../interfaces/program-performance-interfaces";

import { isDRUser, isJOUser } from "../../utils/authFunctions";
import { FeatureFlagEnum, getFeatureFlagList, getFeatureFlagValue } from "../../utils/FeatureToggle";
import { setEveryValueInObject } from "../../utils/objectUtils";
import {
  PATH_DASHBOARD_PP_CAPITAL_COSTS,
  PATH_DASHBOARD_PP_ENERGY_USAGE,
  PATH_DASHBOARD_PP_MAINTENANCE,
  PATH_DASHBOARD_PP_NETWORK_SIZE,
  PATH_DASHBOARD_PP_RELIABILITY,
} from "../../utils/pathConstants";
import {
  getDashboardUpdatedDay,
  getDashboardUpdatedTime,
  PP_DASHBOARD_SECTION_HEADING_NETWORK_SIZE,
  PP_DASHBOARD_SECTION_HEADING_RELIABILITY,
  PP_DASHBOARD_SECTION_HEADING_CAPITAL_COSTS,
} from "../../utils/dashboard";
import { ROUTE_NOT_AUTHORIZED, ROUTE_TECHNICAL_NOTES_PROGRAM_PERFORMANCE } from "../../utils/routeConstants";
import { formatKpiMagnitude } from "../../validation/kpi-magnitude";

import ProgramPerformanceDashboardFilters from "./ProgramPerformanceDashboardFilters";
import { ProgramPerformanceEnergyUsage, ProgramPerformanceMaintenanceCosts } from "./ProgramPerformanceSections";
import DonutChart from "./DonutChart/DonutChart";
import CustomLink from "../Tooltip/tooltips";

import "./ProgramPerformanceDashboard.css";

/**
 * The error Alert component for the Program Performance Dashboard.
 *
 * This component displays at the top of a Program Performance section if there
 * was an error returning one of the metrics.
 *
 * @returns an Alert component.
 */
export const PPDashboardErrorAlert = (): ReactElement => (
  <Alert type="info" headingLevel="h3" noIcon className="pp-dashboard-alert">
    <div className="pp-dashboard-alert__heading">Calculations unavailable</div>
    <div>
      Calculations cannot be completed because either:
      <ol className="pp-dashboard-alert__ol">
        <li>No data matches filters, or,</li>
        <li>Error(s) exist within submitted data.</li>
      </ol>
    </div>
  </Alert>
);

const ProgramPerformanceDashboard = (): ReactElement => {
  /**
   * Set API URL for API calls
   */
  const API_URL = import.meta.env.VITE_API_URL;

  /**
   * Set the ID Token for API calls
   */
  const id_token = localStorage.getItem("id_token");

  const navigate = useNavigate();

  /**
   * State variable for the Dashboard Updated timestamp
   */
  const [dashboardUpdatedTime, setDashboardUpdatedTime] = useState<string>(getDashboardUpdatedTime());
  const [dashboardUpdatedDay, setDashboardUpdatedDay] = useState<string>(getDashboardUpdatedDay());

  /**
   * State variable for JO filters
   */
  const [drFilter, setDRFilter] = useState<string>("All");

  /**
   * State variables for DR filters
   */
  const [stationFilter, setStationFilter] = useState<string>("All");
  const [subrecipientFilter, setSubrecipientFilter] = useState<string>("All");
  const allReportingYearsOption = { value: "All", label: "Program Lifetime" };
  const [reportingYearFilter, setReportingYearFilter] = useState<string>(allReportingYearsOption.value);

  /**
   * State variable for whether the 'Update View' button is disabled.
   *
   * This variable changes if the user has made changes to the filters
   * but not yet submit those changes by clicking 'Update View'.
   */
  const [updateViewDisabled, setUpdateViewDisabled] = useState<boolean>(true);

  /**
   * State variable to check whether the GETDashboardProgramPerformance API call is
   * still executing.
   */
  const [isCapitalCostLoading, setIsCapitalCostsLoading] = useState<boolean>(false);
  const [isMaintenanceLoading, setIsMaintenanceLoading] = useState<boolean>(false);
  const [isReliabilityLoading, setIsReliabilityLoading] = useState<boolean>(false);
  const [isEnergyUsageLoading, setIsEnergyUsageLoading] = useState<boolean>(false);
  const [isNetworkSizeLoading, setIsNetworkSizeLoading] = useState<boolean>(false);

  /**
   * State variable to check whether the GETDashboardProgramPerformance API call failed
   * and returned an error. For example, a 500 error.
   */
  const [dashboardSystemError, setDashboardSystemError] = useState<boolean>(false);

  /**
   * Feature flag management
   * Toggles:
   *  * Reporting Year Dropdown
   *  * Dynamic KPI metric formatting
   *  * Official uptime in Reliability section
   *  * Link to Technical Notes page
   */
  const [drPPDashboardReportingYearFeatureFlag, setDrPPDashboardReportingYearFeatureFlag] = useState<
    boolean | undefined
  >();
  const [drPPDashboardDynamicUnitsFeatureFlag, setDrPPDashboardDynamicUnitsFeatureFlag] = useState<
    boolean | undefined
  >();
  const [drPPDashboardOfficialUptimeFeatureFlag, setDrPPDashboardOfficialUptimeFeatureFlag] = useState<
    boolean | undefined
  >();
  const [technicalNotesDRPPDashboardFeatureFlag, setTechnicalNotesDRPPDashboardFeatureFlag] = useState<
    boolean | undefined
  >();

  /**
   * State variable for the Network Size section data
   */
  const [networkSizeState, setNetworkSizeState] = useState<NetworkSizeInterface>({
    totalStations: "",
    portsAtStations: "",
    l2Ports: "",
    dcfcPorts: "",
    undefinedPorts: "",
  });

  /**
   * State variable that indicates if all of the Network Size section metrics
   * could be returned to the UI.
   *
   * If false, the PPDashboardErrorAlert component will be rendered at the top of the
   * section.
   */
  const [networkSizeMetricsAvailable, setNetworkSizeMetricsAvailable] = useState<boolean>();

  /**
   * State variable for the Reliability section data
   */
  const [reliabilityState, setReliabilityState] = useState<ReliabilityInterface>({
    numberPortsReqMet: "",
    totalPortsReqMet: "",
    percentagePortsReqMet: "",
    percentagePortsReqNotMet: "",
    avgTime: "",
  });

  /**
   * State variable that indicates if all of the Reliability section metrics
   * could be returned to the UI.
   *
   * If false, the PPDashboardErrorAlert component will be rendered at the top of the
   * section.
   */
  const [reliabilityMetricsAvailable, setReliabilityMetricsAvailable] = useState<boolean>();

  /**
   * State variable for the data in the Capital Costs sections
   */
  const [capitalCostsState, setCapitalCostsState] = useState<CapitalCostsInterface>({
    stationCapitalCost: "",
    totalCost: "",
    numberPorts: "",
    numberStations: "",
    federalCost: "",
    nonfederalCost: "",
  });

  /**
   * State variable that indicates if all of the Capital Costs section metrics
   * could be returned to the UI.
   *
   * If false, the PPDashboardErrorAlert component will be rendered at the top of the
   * section.
   */
  const [capitalCostMetricsAvailable, setCapitalCostMetricsAvailable] = useState<boolean>();

  /**
   * State variable that indicates if all of the Maintenance & Repair Costs section metrics
   * could be returned to the UI.
   *
   * If false, the PPDashboardErrorAlert component will be rendered at the top of the
   * section.
   */
  const [maintenanceCostMetricsAvailable, setMaintenanceCostMetricsAvailable] = useState<boolean>();
  const [stationMaintenanceCost, setStationMaintenanceCost] = useState<string>();

  /**
   * State variable for the Energy Usage section data
   */
  const [energyState, setEnergyState] = useState<EnergyUsageInterface>({
    totalChargingSessions: "",
    avgChargingDuration: "",
    stdevChargingSession: "",
    medianChargingSession: "",
    cumulativeEnergy: "",
    avgChargingPower: "",
  });

  /**
   * State variable that indicates if all of the Energy Usage section metrics
   * could be returned to the UI.
   *
   * If false, the PPDashboardErrorAlert component will be rendered at the top of the
   * section.
   */
  const [energyMetricsAvailable, setEnergyMetricsAvailable] = useState<boolean>();

  /**
   * Reliability state chart data
   */
  const reliabilityChartData = [
    {
      key: "Ports meeting 97% Uptime Requirement",
      value: Number(reliabilityState["percentagePortsReqMet"]),
    },
    {
      key: "Ports not meeting 97% Uptime Requirement",
      value: Number(reliabilityState["percentagePortsReqNotMet"]),
    },
  ];

  /**
   * Rounds a decimal to the US dollar format.
   *
   * @param x a decimal in US dollars.
   * @returns the decimal with US dollar formatting, always including 2 decimal places.
   *
   * This function can be removed once the Dynamic Units feature is stable in prod,
   * and its feature toggle is removed as part of tech debt.
   */
  const convertToUSDollars = (x: number) =>
    x
      .toLocaleString("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 0,
      })
      .replace("$", "");

  const removeTrailingZeroCents = (x: string) => x.replace(/\.00$/, "");

  const numberWithCommas = (x: number | string) => x?.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");

  const formatDashboardData = (
    x: number | string | null,
    convertToDollars?: boolean,
    roundToWholeNumber?: boolean,
    metricType?: string,
  ) => {
    const xValue = typeof x === "string" ? parseFloat(x) : x;
    if (drPPDashboardDynamicUnitsFeatureFlag) {
      return formatKpiMagnitude(xValue, metricType);
    } else {
      if (xValue == null) {
        return "--";
      }
      if (convertToDollars) {
        const formattedDataDollars = convertToUSDollars(xValue);
        return removeTrailingZeroCents(formattedDataDollars);
      } else if (roundToWholeNumber) {
        return Math.round(xValue * 100).toString();
      }
      return numberWithCommas(Math.round(Number(xValue)));
    }
  };

  /**
   * Function to handle when a system error, such as a 500 error, occurs.
   *
   * Sets every section's values to null and the dashboardSystemError state
   * variable to true.
   */
  const setDashboardToSystemErrorState = () => {
    const nullNetworkSizeState = setEveryValueInObject(networkSizeState, formatDashboardData(null));
    const nullReliabilityState = setEveryValueInObject(reliabilityState, formatDashboardData(null));
    const nullCapitalCostsState = setEveryValueInObject(capitalCostsState, formatDashboardData(null));
    const nullEnergyUsageState = energyState;
    Object.keys(nullEnergyUsageState).forEach((key) => {
      nullEnergyUsageState[key as keyof typeof nullEnergyUsageState] =
        key === "cumulativeEnergy" || key === "avgChargingPower"
          ? formatDashboardData(null, undefined, undefined, "energy")
          : formatDashboardData(null);
    });

    /**
     * Sets every section's values to null so that they are displayed with "--"
     * rather than blank.
     */
    setNetworkSizeState(nullNetworkSizeState);
    if (isJOUser() || (isDRUser() && drPPDashboardOfficialUptimeFeatureFlag)) {
      setReliabilityState(nullReliabilityState);
    }
    setCapitalCostsState(nullCapitalCostsState);
    setEnergyState(nullEnergyUsageState);

    /**
     * Sets dashboardSystemError state variable to true so that the system error
     * Alert banner will render at the top of the dashboard.
     */
    setDashboardSystemError(true);
  };

  useEffect(() => {
    /**
     * On initial render, get the feature flag list and, using its results,
     * set the feature flag state variables.
     */
    getFeatureFlagList().then((results) => {
      setDrPPDashboardReportingYearFeatureFlag(
        getFeatureFlagValue(results, FeatureFlagEnum.DRPPDashboardReportingYear),
      );
      setDrPPDashboardDynamicUnitsFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.DRPPDashboardDynamicUnits));
      setDrPPDashboardOfficialUptimeFeatureFlag(
        getFeatureFlagValue(results, FeatureFlagEnum.DRPPDashboardOfficialUptime),
      );
      setTechnicalNotesDRPPDashboardFeatureFlag(
        getFeatureFlagValue(results, FeatureFlagEnum.ResourcesTechnicalNotesDRPPDashboard),
      );
    });
  }, []);

  /**
   * Call APIs for dashboard data
   */
  useEffect(() => {
    setIsCapitalCostsLoading(true);
    setIsMaintenanceLoading(true);
    setIsEnergyUsageLoading(true);
    setIsReliabilityLoading(true);
    setIsNetworkSizeLoading(true);

    /**
     * Checks if feature flag values have been set.
     */
    if (
      typeof drPPDashboardReportingYearFeatureFlag !== "undefined" &&
      typeof drPPDashboardDynamicUnitsFeatureFlag !== "undefined"
    ) {
      const drQueryParams = drPPDashboardReportingYearFeatureFlag
        ? `sr_id=${subrecipientFilter}&station=${stationFilter}&year=${reportingYearFilter}`
        : `sr_id=${subrecipientFilter}&station=${stationFilter}`;

      /**
       * Make an API call here to get the program performance data
       */
      const queryParams = isJOUser() ? `dr_id=${drFilter}` : drQueryParams;

      const handle_error = (section: string) => (err: Error | unknown) => {
        if (err instanceof Error && "status" in err) {
          const errorCode = err.status;
          if (errorCode === 403) {
            navigate(ROUTE_NOT_AUTHORIZED);
          } else {
            setDashboardToSystemErrorState();
          }
          console.log(`error loading section ${section}: `, err.message);
        } else {
          console.log(`unknown error loading section ${section}: `, err);
        }
      };

      const handle_finally = (setLoadingState: Dispatch<SetStateAction<boolean>>) => {
        setDashboardUpdatedTime(getDashboardUpdatedTime());
        setDashboardUpdatedDay(getDashboardUpdatedDay());
        setLoadingState(false);
      };

      //#region -c <set fetch events>
      const capital_costs_fetch = fetch(`${API_URL}${PATH_DASHBOARD_PP_CAPITAL_COSTS}?${queryParams}`, {
        method: "GET",
        headers: {
          Authorization: `${id_token}`,
        },
      }).then((response) => response.json());
      const maintenance_fetch = fetch(`${API_URL}${PATH_DASHBOARD_PP_MAINTENANCE}?${queryParams}`, {
        method: "GET",
        headers: {
          Authorization: `${id_token}`,
        },
      }).then((response) => response.json());
      const energy_usage_fetch = fetch(`${API_URL}${PATH_DASHBOARD_PP_ENERGY_USAGE}?${queryParams}`, {
        method: "GET",
        headers: {
          Authorization: `${id_token}`,
        },
      }).then((response) => response.json());
      const reliability_fetch = fetch(`${API_URL}${PATH_DASHBOARD_PP_RELIABILITY}?${queryParams}`, {
        method: "GET",
        headers: {
          Authorization: `${id_token}`,
        },
      }).then((response) => response.json());
      const federally_funded_network_size_fetch = fetch(`${API_URL}${PATH_DASHBOARD_PP_NETWORK_SIZE}?${queryParams}`, {
        method: "GET",
        headers: {
          Authorization: `${id_token}`,
        },
      }).then((response) => response.json());
      //#endregion

      //#region -c <call fetch events in parallell>
      //#region <capital cost fetch>
      capital_costs_fetch
        .then((data) => {
          /**
           * Get data from the API
           */
          const dashboardData = data[0];
          setCapitalCostsState({
            stationCapitalCost: formatDashboardData(dashboardData["average_nevi_capital_cost"], true),
            totalCost: formatDashboardData(dashboardData["deployment_cost"], true),
            numberPorts: formatDashboardData(dashboardData["capital_cost_ports_count"]),
            numberStations: formatDashboardData(dashboardData["capital_cost_stations_count"]),
            federalCost: formatDashboardData(dashboardData["federal_funding"], true),
            nonfederalCost: formatDashboardData(dashboardData["nonfederal_funding"], true),
          });
          setCapitalCostMetricsAvailable(dashboardData["capital_cost_metrics_available"]);
        })
        .catch(handle_error("Capital Costs"))
        .finally(() => {
          handle_finally(setIsCapitalCostsLoading);
        });
      //#endregion <capital cost fetch>

      //#region <maintenance fetch>
      maintenance_fetch
        .then((data) => {
          /**
           * Get data from the API
           */
          const dashboardData = data[0];
          setStationMaintenanceCost(formatDashboardData(dashboardData["monthly_avg_maintenance_repair_cost"], true));
          setMaintenanceCostMetricsAvailable(dashboardData["maintenance_cost_metrics_available"]);
        })
        .catch(handle_error("Maintenance"))
        .finally(() => {
          handle_finally(setIsMaintenanceLoading);
        });
      //#endregion <maintenance fetch>

      //#region <energy usage fetch>
      energy_usage_fetch
        .then((data) => {
          /**
           * Get data from the API
           */
          const dashboardData = data[0];
          /**
           * Set data for the Energy Usage section
           */
          setEnergyState({
            totalChargingSessions: formatDashboardData(dashboardData["total_charging_sessions"]),
            avgChargingDuration: formatDashboardData(dashboardData["average_charging_duration"]),
            stdevChargingSession: formatDashboardData(dashboardData["stdev_charging_session"]),
            medianChargingSession: formatDashboardData(dashboardData["median_charging_session"]),
            cumulativeEnergy: formatDashboardData(
              dashboardData["cumulative_energy_federal_ports"],
              undefined,
              undefined,
              "energy",
            ),
            avgChargingPower: formatDashboardData(
              dashboardData["average_charging_power"],
              undefined,
              undefined,
              "energy",
            ),
          });
          setEnergyMetricsAvailable(dashboardData["energy_metrics_available"]);
        })
        .catch(handle_error("Energy Usage"))
        .finally(() => {
          handle_finally(setIsEnergyUsageLoading);
        });
      //#endregion <energy usage fetch>

      //#region <reliability fetch>
      reliability_fetch
        .then((data) => {
          /**
           * Get data from the API
           */
          const dashboardData = data[0];
          // Reliability
          if (isJOUser() || (isDRUser() && drPPDashboardOfficialUptimeFeatureFlag)) {
            /**
             * Set data for the Reliability section
             *
             * JO users see reliability metrics using unofficial uptime.
             * DR users see reliability metrics using official uptime.
             */
            const uptimeMetric = isJOUser() ? "unofficial_uptime" : "official_uptime";

            setReliabilityState({
              numberPortsReqMet: formatDashboardData(dashboardData[uptimeMetric]["num_ports_meeting_uptime_req"]),
              totalPortsReqMet: formatDashboardData(dashboardData[uptimeMetric]["total_ports_with_uptime_activity"]),
              percentagePortsReqMet: formatDashboardData(
                dashboardData[uptimeMetric]["percentage_ports_meeting_uptime_req"],
                undefined,
                true,
                "percentage",
              ),
              percentagePortsReqNotMet: formatDashboardData(
                dashboardData[uptimeMetric]["percentage_ports_not_meeting_uptime_req"],
                undefined,
                true,
                "percentage",
              ),
              /**
               * This is only metric in this section that is not dependent on uptime.
               * Therefore, it's not nested under 'official_uptime' or 'unofficial_uptime'.
               */
              avgTime: formatDashboardData(dashboardData["avg_outage"]),
            });
            setReliabilityMetricsAvailable(dashboardData[uptimeMetric]["reliability_metrics_available"]);
          }
        })
        .catch(handle_error("Reliability"))
        .finally(() => {
          handle_finally(setIsReliabilityLoading);
        });
      //#endregion <reliability fetch>

      //#region <federally funded network size fetch fetch>
      federally_funded_network_size_fetch
        .then((data) => {
          /**
           * Get data from the API
           */
          const dashboardData = data[0];
          /**
           * Set data for the Network Size section
           */
          setNetworkSizeState({
            totalStations: formatDashboardData(dashboardData["total_stations"]),
            portsAtStations: formatDashboardData(dashboardData["total_ports"]),
            l2Ports: formatDashboardData(dashboardData["l2_ports"]),
            dcfcPorts: formatDashboardData(dashboardData["dcfc_ports"]),
            undefinedPorts: formatDashboardData(dashboardData["undefined_ports"]),
          });
          setNetworkSizeMetricsAvailable(dashboardData["station_data_available"]);
        })
        .catch(handle_error("Federally Funded Network Size"))
        .finally(() => {
          handle_finally(setIsNetworkSizeLoading);
        });
      //#endregion <federally funded network size fetch>
      //#endregion <call fetch events in parallell>
    }
    /**
     * Re-run the API call when one of the filters' value changes
     * and the 'Update View' button is clicked.
     */
  }, [
    drFilter,
    stationFilter,
    subrecipientFilter,
    reportingYearFilter,
    drPPDashboardReportingYearFeatureFlag,
    drPPDashboardDynamicUnitsFeatureFlag,
  ]);
  //#region HTML object
  return (
    <div id="program-performance-dashboard">
      <GridContainer className="program-performance-container">
        {dashboardSystemError && (
          <Alert type="error" headingLevel="h3" className="user-error-banner" heading="An Error Occurred">
            An error occurred when attempting to retrieve the program performance metrics. Please try again later, if
            the problem persists please reach out to EV-ChART help.
          </Alert>
        )}
        <Grid row>
          <Grid col>
            <h2 className="program-performance-header">Program Performance</h2>
          </Grid>
          {technicalNotesDRPPDashboardFeatureFlag && (
            <Grid col="auto">
              <div>
                <Button
                  type="button"
                  className="link-styling"
                  onClick={() => navigate(ROUTE_TECHNICAL_NOTES_PROGRAM_PERFORMANCE)}
                >
                  How are these metrics calculated?
                </Button>
              </div>
            </Grid>
          )}
        </Grid>
        <Grid row>
          <Grid col>
            <div className="pp-dashboard-time fixed-width-tooltip">
              <div className="program-performance-time">Dashboard Updated: {dashboardUpdatedTime}</div>
              <Tooltip
                label={
                  "Timestamp indicates the most recent refresh of the data displayed on the dashboard. Changing the parameters or reloading the page triggers a new timestamp."
                }
                asCustom={CustomLink}
              >
                <Icon.InfoOutline />
              </Tooltip>
            </div>
          </Grid>
        </Grid>
        <Grid row gap className="program-performance-overview-text">
          <Grid col={12}>
            <p>
              The program performance dashboard tracks EV charging projects funded with Title 23 funds.
              Non-federally funded stations and ports are excluded from the dashboard.
            </p>
          </Grid>
        </Grid>
        <ProgramPerformanceDashboardFilters
          drFilter={drFilter}
          setDRFilter={setDRFilter}
          stationFilter={stationFilter}
          setStationFilter={setStationFilter}
          subrecipientFilter={subrecipientFilter}
          setSubrecipientFilter={setSubrecipientFilter}
          reportingYearFilter={reportingYearFilter}
          setReportingYearFilter={setReportingYearFilter}
          allReportingYearsOption={allReportingYearsOption}
          updateViewDisabled={updateViewDisabled}
          setUpdateViewDisabled={setUpdateViewDisabled}
        />
        {typeof drPPDashboardReportingYearFeatureFlag === "undefined" ||
        typeof drPPDashboardDynamicUnitsFeatureFlag === "undefined" ? (
          <div className="pp-dashboard-spinner-container">
            <div className="pp-dashboard-spinner">
              <Spinner />
            </div>
            <div className="pp-dashboard-spinner-content text-center">
              <p>Updating Dashboard View</p>
            </div>
          </div>
        ) : (
          <div>
            <Grid row gap className="pp-dashboard-row">
              <Grid col={4}>
                <Grid row>
                  <Grid col={12}>
                    <div className="pp-dashboard-section-heading fixed-width-tooltip">
                      <div className="pp-dashboard-section-heading-text">
                        {PP_DASHBOARD_SECTION_HEADING_NETWORK_SIZE}
                      </div>
                      <Tooltip
                        label={
                          "All Network Size metrics are calculated using details provided at registration of each federally-funded station. If any data appears incorrect, add or edit station details."
                        }
                        asCustom={CustomLink}
                      >
                        <Icon.InfoOutline />
                      </Tooltip>
                    </div>
                  </Grid>
                </Grid>
                {!networkSizeMetricsAvailable && <PPDashboardErrorAlert />}
                {isNetworkSizeLoading ? (
                  <div className="pp-dashboard-spinner-container">
                    <div className="pp-dashboard-spinner">
                      <Spinner />
                    </div>
                    <div className="pp-dashboard-spinner-content text-center">
                      <p>Updating Dashboard View</p>
                    </div>
                  </div>
                ) : (
                  <div className={updateViewDisabled ? "" : "text-base-light"}>
                    <Grid row>
                      <Grid col={12}>
                        <div className="pp-dashboard-large-stat">{networkSizeState["totalStations"]}</div>
                        <div className="pp-dashboard-stat-label pp-dashboard-large-stat-label">
                          Total number of stations as of {dashboardUpdatedDay}
                        </div>
                      </Grid>
                    </Grid>
                    <Grid row>
                      <Grid col={12}>
                        <div className="pp-dashboard-large-stat">{networkSizeState["portsAtStations"]}</div>
                        <div className="pp-dashboard-stat-label pp-dashboard-large-stat-label">
                          Total number of ports as of {dashboardUpdatedDay}
                        </div>
                      </Grid>
                    </Grid>
                    <Grid row className="pp-dashboard-small-stat-row">
                      <Grid col={3}>
                        <div className="pp-dashboard-small-stat pull-right">{networkSizeState["l2Ports"]}</div>
                      </Grid>
                      <Grid col={9}>
                        <div className="pp-dashboard-stat-label">L2 ports</div>
                      </Grid>
                    </Grid>
                    <Grid row className="pp-dashboard-small-stat-row">
                      <Grid col={3}>
                        <div className="pp-dashboard-small-stat pull-right">{networkSizeState["dcfcPorts"]}</div>
                      </Grid>
                      <Grid col={9}>
                        <div className="pp-dashboard-stat-label">DCFC ports</div>
                      </Grid>
                    </Grid>
                    <Grid row className="pp-dashboard-small-stat-row">
                      <Grid col={3}>
                        <div className="pp-dashboard-small-stat pull-right">{networkSizeState["undefinedPorts"]}</div>
                      </Grid>
                      <Grid col={9}>
                        <div className="pp-dashboard-stat-label">Ports that are undefined</div>
                      </Grid>
                    </Grid>
                  </div>
                )}
              </Grid>
              <Grid col={8}>
                {/**
                 * Update layout based on the user.
                 *
                 * If JO or (DR and official uptime feature flag is true), display the
                 * Reliability section. Else, display the Energy Usage section in the
                 * place of the Reliability section.
                 *
                 * This logic continues throughout the page to change the layout.
                 */}
                {isJOUser() || (isDRUser() && drPPDashboardOfficialUptimeFeatureFlag) ? (
                  <>
                    <Grid row className="pp-dashboard-reliability-section">
                      <Grid col={12}>
                        <div className="pp-dashboard-section-heading fixed-width-tooltip">
                          <div className="pp-dashboard-section-heading-text">
                            {PP_DASHBOARD_SECTION_HEADING_RELIABILITY}
                          </div>
                          <Tooltip
                            label={
                              "All Reliability metrics are calculated using details provided at registration of each station and Module 4 (Outages) data. Module 3 (Uptime) data is used for stations that have been operational for at least one year."
                            }
                            asCustom={CustomLink}
                          >
                            <Icon.InfoOutline />
                          </Tooltip>
                        </div>
                      </Grid>
                    </Grid>
                    {isJOUser() && (
                      <Alert
                        type="info"
                        headingLevel="h3"
                        noIcon
                        className="pp-dashboard-alert pp-dashboard-alert--reliability"
                      >
                        <div className="pp-dashboard-alert__heading">
                          The following metrics are not considered &quot;official&quot; uptime calculations.
                        </div>
                        <div>
                          Excluded outages are not included in uptime calculations for stations operational less than
                          one (1) year, resulting in preliminary values that may be artificially low.
                        </div>
                      </Alert>
                    )}
                    {!reliabilityMetricsAvailable && <PPDashboardErrorAlert />}
                    {isReliabilityLoading ? (
                      <div className="pp-dashboard-spinner-container">
                        <div className="pp-dashboard-spinner">
                          <Spinner />
                        </div>
                        <div className="pp-dashboard-spinner-content text-center">
                          <p>Updating Dashboard View</p>
                        </div>
                      </div>
                    ) : (
                      <Grid row gap className="pp-dashboard-reliability-data">
                        <Grid col={6} className={updateViewDisabled ? "" : "text-base-light"}>
                          <Grid row className="pp-dashboard-bottom-border">
                            <Grid col={12}>
                              <div className="pp-dashboard-stat-flex">
                                <div className="pp-dashboard-large-stat">{reliabilityState["numberPortsReqMet"]}</div>
                                <div className="pp-dashboard-stat-large-helper-text">
                                  (of {reliabilityState["totalPortsReqMet"]})
                                </div>
                              </div>
                              <div className="pp-dashboard-stat-label pp-dashboard-large-stat-label">
                                Federally funded ports meeting 97% uptime requirement
                              </div>
                            </Grid>
                          </Grid>
                          <Grid row className="pp-dashboard-bottom-border">
                            <Grid col={12}>
                              <div className="pp-dashboard-large-stat">
                                {reliabilityState["percentagePortsReqMet"]}%
                              </div>
                              <div className="pp-dashboard-stat-label pp-dashboard-large-stat-label">
                                Percentage of federally funded ports meeting 97% uptime requirement
                              </div>
                            </Grid>
                          </Grid>
                          <Grid row>
                            <Grid col={12}>
                              <div className="pp-dashboard-large-stat">{reliabilityState["avgTime"]} Minutes</div>
                              <div className="pp-dashboard-stat-label pp-dashboard-large-stat-label">
                                Average outage duration per event
                              </div>
                            </Grid>
                          </Grid>
                        </Grid>
                        <Grid col={6} className={updateViewDisabled ? "" : "text-base-light"}>
                          <Grid row>
                            <Grid col={12}>
                              <div className="pp-dashboard-chart-title">Ports meeting 97% Uptime Requirement</div>
                            </Grid>
                          </Grid>
                          <Grid row className="reliability-donut-chart">
                            <Grid col={12}>
                              <DonutChart
                                data={reliabilityChartData}
                                height={120}
                                width={120}
                                colors={updateViewDisabled ? undefined : ["#A9AEB1"]}
                              />
                            </Grid>
                          </Grid>
                          <Grid row>
                            <Grid col={12}>
                              <div className="pp-dashboard-stat-flex">
                                <div
                                  className={`pp-dashboard-legend-circle ${updateViewDisabled ? "positive" : "disabled"}`}
                                />
                                <div className="pp-dashboard-legend-text">
                                  {reliabilityState["percentagePortsReqMet"]}%
                                </div>
                              </div>
                            </Grid>
                          </Grid>
                          <Grid row>
                            <Grid col={12}>
                              <div className="pp-dashboard-stat-label pp-dashboard-legend-label">
                                Federally funded ports meeting 97% uptime requirement
                              </div>
                            </Grid>
                          </Grid>
                          <Grid row>
                            <Grid col={12}>
                              <div className="pp-dashboard-stat-flex">
                                <div
                                  className={`pp-dashboard-legend-circle ${updateViewDisabled ? "negative" : "disabled"}`}
                                />
                                <div className="pp-dashboard-legend-text">
                                  {reliabilityState["percentagePortsReqNotMet"]}%
                                </div>
                              </div>
                            </Grid>
                          </Grid>
                          <Grid row>
                            <Grid col={12}>
                              <div className="pp-dashboard-stat-label pp-dashboard-legend-label">
                                Federally funded ports not meeting 97% uptime requirement
                              </div>
                            </Grid>
                          </Grid>
                        </Grid>
                      </Grid>
                    )}
                  </>
                ) : (
                  <ProgramPerformanceEnergyUsage
                    drFilter={drFilter}
                    energyState={energyState}
                    energyMetricsAvailable={energyMetricsAvailable}
                    updateViewDisabled={updateViewDisabled}
                    drPPDashboardDynamicUnitsFeatureFlag={drPPDashboardDynamicUnitsFeatureFlag}
                    isLoading={isEnergyUsageLoading}
                  />
                )}
              </Grid>
            </Grid>
            <Grid row gap className="pp-dashboard-row">
              <Grid col={4}>
                <Grid row className="pp-dashboard-costs-section">
                  <Grid col={12}>
                    <div className="pp-dashboard-section-heading fixed-width-tooltip">
                      <div className="pp-dashboard-section-heading-text">
                        {PP_DASHBOARD_SECTION_HEADING_CAPITAL_COSTS}
                      </div>
                      <Tooltip
                        label={
                          "Capital cost calculations are developed using details provided at registration of each station, as well as Module 9 data."
                        }
                        asCustom={CustomLink}
                      >
                        <Icon.InfoOutline />
                      </Tooltip>
                    </div>
                  </Grid>
                </Grid>
                {!capitalCostMetricsAvailable && <PPDashboardErrorAlert />}
                {isCapitalCostLoading ? (
                  <div className="pp-dashboard-spinner-container">
                    <div className="pp-dashboard-spinner">
                      <Spinner />
                    </div>
                    <div className="pp-dashboard-spinner-content text-center">
                      <p>Updating Dashboard View</p>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className={updateViewDisabled ? "" : "text-base-light"}>
                      <Grid row className="pp-dashboard-bottom-border">
                        <Grid col={12}>
                          <div className="pp-dashboard-stat-flex">
                            <div className="pp-dashboard-large-stat">${capitalCostsState["stationCapitalCost"]}</div>
                            <div className="pp-dashboard-stat-large-helper-text">per NEVI station</div>
                          </div>
                          <div className="pp-dashboard-stat-label pp-dashboard-large-stat-label">
                            Average capital cost for NEVI stations*
                          </div>
                        </Grid>
                      </Grid>
                      <Grid row>
                        <Grid col={12}>
                          <div className="pp-dashboard-large-stat">${capitalCostsState["totalCost"]}</div>
                          <div className="pp-dashboard-stat-label pp-dashboard-large-stat-label">
                            Cost to deploy {capitalCostsState["numberPorts"]} ports across{" "}
                            {capitalCostsState["numberStations"]} stations*
                          </div>
                        </Grid>
                      </Grid>
                      <Grid row className="pp-dashboard-small-stat-row">
                        <Grid col={5}>
                          <div className="pp-dashboard-small-stat pull-right">${capitalCostsState["federalCost"]}</div>
                        </Grid>
                        <Grid col={7}>
                          <div className="pp-dashboard-stat-label">Federal funding</div>
                        </Grid>
                      </Grid>
                      <Grid row className="pp-dashboard-small-stat-row">
                        <Grid col={5}>
                          <div className="pp-dashboard-small-stat pull-right">
                            ${capitalCostsState["nonfederalCost"]}
                          </div>
                        </Grid>
                        <Grid col={7}>
                          <div className="pp-dashboard-stat-label">Non-federal funding</div>
                        </Grid>
                      </Grid>
                    </div>
                    <Grid row className="pp-description-row">
                      <Grid col={12} className="pp-dashboard-stat-label">
                        * Calculation excludes real property acquisition and DER (Distributed Energy Resource)
                        acquisition and installation costs
                      </Grid>
                    </Grid>
                  </>
                )}
                {/**
                 * If JO or (DR and official uptime feature flag is true), display the
                 * Maintenance & Repair Costs section below the Capital Costs section.
                 * Else, display it in the bottom right section.
                 */}
                {(isJOUser() || (isDRUser() && drPPDashboardOfficialUptimeFeatureFlag)) && (
                  <div className="jo-pp-dashboard-maintenance-costs">
                    <ProgramPerformanceMaintenanceCosts
                      stationMaintenanceCost={stationMaintenanceCost}
                      maintenanceCostMetricsAvailable={maintenanceCostMetricsAvailable}
                      updateViewDisabled={updateViewDisabled}
                      isLoading={isMaintenanceLoading}
                    />
                  </div>
                )}
              </Grid>
              {/**
               * If JO or (DR and official uptime feature flag is true), display the
               * Energy Usage. Else, display the Maintenance & Repair Costs section.
               */}
              {isJOUser() || (isDRUser() && drPPDashboardOfficialUptimeFeatureFlag) ? (
                <Grid col={8}>
                  <ProgramPerformanceEnergyUsage
                    drFilter={drFilter}
                    energyState={energyState}
                    energyMetricsAvailable={!!energyMetricsAvailable}
                    updateViewDisabled={updateViewDisabled}
                    drPPDashboardDynamicUnitsFeatureFlag={drPPDashboardDynamicUnitsFeatureFlag}
                    isLoading={isEnergyUsageLoading}
                  />
                </Grid>
              ) : (
                <Grid col={4}>
                  <ProgramPerformanceMaintenanceCosts
                    stationMaintenanceCost={stationMaintenanceCost}
                    maintenanceCostMetricsAvailable={maintenanceCostMetricsAvailable}
                    updateViewDisabled={updateViewDisabled}
                    isLoading={isMaintenanceLoading}
                  />
                </Grid>
              )}
            </Grid>
          </div>
        )}
      </GridContainer>
    </div>
  );
  //#endregion HTML object
};

export default ProgramPerformanceDashboard;
