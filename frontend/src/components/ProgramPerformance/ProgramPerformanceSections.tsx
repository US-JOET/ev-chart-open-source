/**
 * Two sections of the Program Performance Dashboard: Maintenance & Repair Costs and Energy Usage.
 * The separate components enable conditional rendering of the sections based on the user.
 * @packageDocumentation
 **/
import React, { ReactElement } from "react";

import { Grid, Icon, Spinner, Tooltip } from "evchartstorybook";

import { EnergyUsageInterface } from "../../interfaces/program-performance-interfaces";
import {
  PP_DASHBOARD_SECTION_HEADING_ENERGY_USAGE,
  PP_DASHBOARD_SECTION_HEADING_MAINTENANCE_REPAIR_COSTS,
} from "../../utils/dashboard";
import { PPDashboardErrorAlert } from "./ProgramPerformanceDashboard";

import CustomLink from "../Tooltip/tooltips";

interface ProgramPerformanceMaintenanceCostsProps {
  /**
   * The station maintenance Cost.
   */
  stationMaintenanceCost: string | undefined;
  /**
   * The state variables for whether there is Maintenance & Repair Costs data.
   *
   * If true, all metrics in the section are returned.
   * If false, one of the metrics is null and an error will be displayed to the user.
   */
  maintenanceCostMetricsAvailable: boolean | undefined;
  /**
   * The state variable for whether the 'Update View' button is disabled.
   */
  updateViewDisabled: boolean;
  /**
   * Used to determine if spinner is added to grid
   */
  isLoading: boolean | undefined;
}

export const ProgramPerformanceMaintenanceCosts: React.FC<ProgramPerformanceMaintenanceCostsProps> = ({
  stationMaintenanceCost,
  maintenanceCostMetricsAvailable,
  updateViewDisabled,
  isLoading,
}): ReactElement => {
  return (
    <>
      <Grid row className="pp-dashboard-costs-section">
        <Grid col={12}>
          <div className="pp-dashboard-section-heading fixed-width-tooltip">
            <div className="pp-dashboard-section-heading-text">
              {PP_DASHBOARD_SECTION_HEADING_MAINTENANCE_REPAIR_COSTS}
            </div>
            <Tooltip
              label={
                "Maintenance & Repair cost calculations are developed using details provided at registration of each station, as well as Module 5 data."
              }
              asCustom={CustomLink}
            >
              <Icon.InfoOutline />
            </Tooltip>
          </div>
        </Grid>
      </Grid>
      {!maintenanceCostMetricsAvailable && <PPDashboardErrorAlert />}
      {isLoading ? (
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
          <Grid row className={updateViewDisabled ? "" : "text-base-light"}>
            <Grid col={12}>
              <div className="pp-dashboard-stat-flex">
                <div className="pp-dashboard-large-stat">${stationMaintenanceCost}</div>
                <div className="pp-dashboard-stat-large-helper-text">per station</div>
              </div>
              <div className="pp-dashboard-stat-label pp-dashboard-large-stat-label">
                Average monthly maintenance & repair cost for stations**
              </div>
            </Grid>
          </Grid>
          <Grid row className="pp-description-row">
            <Grid col={12} className="pp-dashboard-stat-label">
              ** Calculation excludes maintenance and repair costs reported as a total cost from a
              &quot;charging-as-a-service&quot; agreement
            </Grid>
          </Grid>
        </>
      )}
    </>
  );
};

interface ProgramPerformanceEnergyUsageProps {
  /**
   * The state variable for the value of the DR filter
   */
  drFilter: string;
  /**
   * The state variable for the Energy Usage section.
   */
  energyState: EnergyUsageInterface;
  /**
   * The state variables for whether there is Energy Usage data.
   *
   * If true, all metrics in the section are returned.
   * If false, one of the metrics is null and an error will be displayed to the user.
   */
  energyMetricsAvailable: boolean | undefined;
  /**
   * The state variable for whether the 'Update View' button is disabled.
   */
  updateViewDisabled: boolean;
  /**
   * The state variable for the DR PP Dashboard Dynamic Units feature flag.
   * Toggles the Dynamic KPI metric formatting
   */
  drPPDashboardDynamicUnitsFeatureFlag: boolean;

  /**
   * Used to add spinner to the grid
   */
  isLoading: boolean | undefined;
}

export const ProgramPerformanceEnergyUsage: React.FC<ProgramPerformanceEnergyUsageProps> = ({
  energyState,
  energyMetricsAvailable,
  updateViewDisabled,
  drPPDashboardDynamicUnitsFeatureFlag,
  isLoading,
}): ReactElement => {
  return (
    <>
      <Grid row className="pp-dashboard-energy-usage-section">
        <Grid col={12}>
          <div className="pp-dashboard-section-heading fixed-width-tooltip">
            <div className="pp-dashboard-section-heading-text">{PP_DASHBOARD_SECTION_HEADING_ENERGY_USAGE}</div>
            <Tooltip
              label={
                "Energy usage calculations are developed using details provided at registration of each station, as well as Module 2 data."
              }
              asCustom={CustomLink}
            >
              <Icon.InfoOutline />
            </Tooltip>
          </div>
        </Grid>
      </Grid>
      {!energyMetricsAvailable && <PPDashboardErrorAlert />}
      {isLoading ? (
        <div className="pp-dashboard-spinner-container">
          <div className="pp-dashboard-spinner">
            <Spinner />
          </div>
          <div className="pp-dashboard-spinner-content text-center">
            <p>Updating Dashboard View</p>
          </div>
        </div>
      ) : (
        <Grid row gap className={updateViewDisabled ? "" : "text-base-light"}>
          <Grid col={6}>
            <Grid row className="pp-dashboard-bottom-border">
              <Grid col={12}>
                <div className="pp-dashboard-stat-flex">
                  <div className="pp-dashboard-large-stat">{energyState["totalChargingSessions"]}</div>
                </div>
                <div className="pp-dashboard-stat-label pp-dashboard-large-stat-label">
                  Total number of charging sessions
                </div>
              </Grid>
            </Grid>
            <Grid row>
              <Grid col={12}>
                <div className="pp-dashboard-large-stat">{energyState["avgChargingDuration"]} Minutes</div>
                <div className="pp-dashboard-stat-label pp-dashboard-large-stat-label">
                  Average of charging session duration
                </div>
              </Grid>
            </Grid>
            <Grid row className="pp-dashboard-small-stat-row">
              <Grid col={3}>
                <div className="pp-dashboard-small-stat pull-right">{energyState["stdevChargingSession"]} Min</div>
              </Grid>
              <Grid col={9}>
                <div className="pp-dashboard-stat-label">Standard deviation of charging session duration</div>
              </Grid>
            </Grid>
            <Grid row className="pp-dashboard-small-stat-row">
              <Grid col={3}>
                <div className="pp-dashboard-small-stat pull-right">{energyState["medianChargingSession"]} Min</div>
              </Grid>
              <Grid col={9}>
                <div className="pp-dashboard-stat-label">Median of charging session duration</div>
              </Grid>
            </Grid>
          </Grid>
          <Grid col={6}>
            <Grid row className="pp-dashboard-bottom-border">
              <Grid col={12}>
                <div className="pp-dashboard-stat-flex">
                  <div className="pp-dashboard-large-stat">
                    {energyState["cumulativeEnergy"]}
                    {drPPDashboardDynamicUnitsFeatureFlag ? "Wh" : " kWh"}
                  </div>
                </div>
                <div className="pp-dashboard-stat-label pp-dashboard-large-stat-label">
                  Cumulative energy dispensed by federally funded ports
                </div>
              </Grid>
            </Grid>
            <Grid row>
              <Grid col={12}>
                <div className="pp-dashboard-stat-flex">
                  <div className="pp-dashboard-large-stat">
                    {energyState["avgChargingPower"]}
                    {drPPDashboardDynamicUnitsFeatureFlag ? "W" : " kW"}
                  </div>
                </div>
                <div className="pp-dashboard-stat-label pp-dashboard-large-stat-label">
                  Average peak power per charging session
                </div>
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      )}
    </>
  );
};
