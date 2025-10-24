/**
 * Page displaying technical notes for program performance calculations.
 * @packageDocumentation
 **/
import React, { ReactNode } from "react";

import { Breadcrumb, BreadcrumbBar, BreadcrumbLink, Grid, GridContainer, Table } from "evchartstorybook";

import { formatModuleNameLabel } from "../../../utils/ModuleName";
import {
  getDashboardUpdatedDay,
  PP_DASHBOARD_SECTION_HEADING_CAPITAL_COSTS,
  PP_DASHBOARD_SECTION_HEADING_ENERGY_USAGE,
  PP_DASHBOARD_SECTION_HEADING_MAINTENANCE_REPAIR_COSTS,
  PP_DASHBOARD_SECTION_HEADING_NETWORK_SIZE,
  PP_DASHBOARD_SECTION_HEADING_RELIABILITY,
} from "../../../utils/dashboard";
import { ROUTE_HOME } from "../../../utils/routeConstants";

import "./TechnicalNotesProgramPerformance.css";

enum CalculationExclusions {
  GENERAL_NON_FED_FUNDED_STATIONS_PORTS = "Non-federally funded stations and ports.",
  GENERAL_DATA_NOT_SUBMITTED_OR_APPROVED = 'Any data apart of a submission with a status other than "Submitted" or "Approved".',
  GENERAL_DATA_UNREGISTERED_PORTS = "Any ports within a data submission that have not been registered to a Station.",

  RELIABILITY_OP_LESS_THAN_YEAR = "Stations operational for less than one year, based on the operational date given in the Station Registration form, from today's date.",
  RELIABILITY_UPTIME_LESS_THAN_YEAR = "If the time period between Uptime Reporting Start Date and Uptime Reporting End Date is less than a year.",
  RELIABILITY_UPTIME_START_BEFORE_OP_DATE = "If the Uptime Reporting Start Date occurs before the Station's operational date, as defined in the Station Registration form.",
  RELIABILITY_OUTAGES_ERROR_SHORT = "Outages with zero or negative duration length.",

  SESSIONS_ERROR_SHORT = "Charging sessions with zero or negative duration length.",
  SESSIONS_ERROR_LONG = "Charging sessions with duration length of greater than one day.",

  CAP_COSTS_STATIONS_MISSING_DATA = "Stations that do not have data submitted for each of the following costs: total equipment, equipment installation, distribution upgrade and utility connection costs.",
  CAP_COSTS_PROPERTY_RESOURCE_COSTS = "Total property acquisition and distributed energy resource acquisition and installation costs.",
  CAP_COSTS_NON_NEVI_STATIONS = 'Stations that do not have "NEVI" federal funding type in EV-ChART.',

  REPAIR_COSTS_FUTURE_OP_DATA = "If the operational date, as defined in the Station Registration, has a year that is later then the reporting year.",
  REPAIR_COSTS_CHARGE_AS_SERVICE = "If maintenance and repair costs are reported as a total cost from a charging-as-a-service agreement.",
}

interface TechnicalNotesPPDashboardCategoryCalculationRow {
  calculation: string;
  description: ReactNode;
  exclusions?: CalculationExclusions[];
  modules_referenced: string;
}

interface TechnicalNotesPPDashboardCategory {
  category: string;
  exclusions: CalculationExclusions[];
  calculations: TechnicalNotesPPDashboardCategoryCalculationRow[];
}

function TechnicalNotesProgramPerformance() {
  /**
   *  Variable for dashboard updated day
   */
  const dashboardUpdatedDay = getDashboardUpdatedDay();

  /**
   * Breadcrumb bar for page
   * @returns the breadcrumb bar
   */
  const DefaultBreadcrumb = (): React.ReactElement => (
    <BreadcrumbBar>
      <Breadcrumb>
        <BreadcrumbLink href={ROUTE_HOME}>
          <span>Home</span>
        </BreadcrumbLink>
      </Breadcrumb>
      <Breadcrumb current>
        <span>How are the Program Performance metrics calculated?</span>
      </Breadcrumb>
    </BreadcrumbBar>
  );

  /**
   * Set the columns for the table
   */
  const columnHeaders: { key: keyof TechnicalNotesPPDashboardCategoryCalculationRow; label: string }[] = [
    { key: "calculation", label: "Calculation" },
    { key: "modules_referenced", label: "Modules Referenced" },
    { key: "description", label: "Calculation Description" },
  ];

  const formattedModuleLabels = (moduleIds: number | number[]): string => {
    if (typeof moduleIds === "number")
      moduleIds = [moduleIds];

    return moduleIds.map(moduleId => formatModuleNameLabel(moduleId)).join(", ");
  };

  const tableContent: TechnicalNotesPPDashboardCategory[] = [
    {
      category: PP_DASHBOARD_SECTION_HEADING_NETWORK_SIZE,
      exclusions: [
        CalculationExclusions.GENERAL_NON_FED_FUNDED_STATIONS_PORTS,
      ],
      calculations: [
        {
          calculation: `Total number of stations as of ${dashboardUpdatedDay}`,
          modules_referenced: formattedModuleLabels(1),
          description: "The count of stations that have at least one federally funded port.",
        },
        {
          calculation: `Total number of ports as of ${dashboardUpdatedDay}`,
          modules_referenced: formattedModuleLabels(1),
          description: "The count of federally funded ports across all stations.",
        },
        {
          calculation: "L2 Ports",
          modules_referenced: formattedModuleLabels(1),
          description: "The count of federally funded L2 ports across all stations.",
        },
        {
          calculation: "DCFC Ports",
          modules_referenced: formattedModuleLabels(1),
          description: "The count of federally funded DCFC ports across all stations.",
        },
        {
          calculation: "Ports that are undefined",
          modules_referenced: formattedModuleLabels(1),
          description: "The count of undefined federally funded ports across all stations.",
        },
      ],
    },
    {
      category: PP_DASHBOARD_SECTION_HEADING_RELIABILITY,
      exclusions: [
        CalculationExclusions.GENERAL_NON_FED_FUNDED_STATIONS_PORTS,
        CalculationExclusions.GENERAL_DATA_NOT_SUBMITTED_OR_APPROVED,
        CalculationExclusions.GENERAL_DATA_UNREGISTERED_PORTS,
      ],
      calculations: [
        {
          calculation: "(Percentage of) federally funded ports meeting 97% uptime requirement",
          modules_referenced: formattedModuleLabels([1, 3]),
          exclusions: [
            CalculationExclusions.RELIABILITY_OP_LESS_THAN_YEAR,
            CalculationExclusions.RELIABILITY_UPTIME_LESS_THAN_YEAR,
            CalculationExclusions.RELIABILITY_UPTIME_START_BEFORE_OP_DATE,
          ],
          description: "The count or percentage of port IDs at stations that have been operational for at least one year and have an uptime of greater than 97% reported in the most recent reporting period. Uptime is calculated in accordance with the equation in 23 CFR 680.116(b)(3) in the EV-ChART Data Format and Preparation Guidance.",
        },
        {
          calculation: "Average outage duration per event",
          modules_referenced: formattedModuleLabels([1, 4]),
          exclusions: [
            CalculationExclusions.RELIABILITY_OUTAGES_ERROR_SHORT,
          ],
          description: "The average duration of outage events.",
        },
      ],
    },
    {
      category: PP_DASHBOARD_SECTION_HEADING_ENERGY_USAGE,
      exclusions: [
        CalculationExclusions.GENERAL_NON_FED_FUNDED_STATIONS_PORTS,
        CalculationExclusions.GENERAL_DATA_NOT_SUBMITTED_OR_APPROVED,
        CalculationExclusions.GENERAL_DATA_UNREGISTERED_PORTS,
        CalculationExclusions.SESSIONS_ERROR_SHORT,
        CalculationExclusions.SESSIONS_ERROR_LONG,
      ],
      calculations: [
        {
          calculation: "Total number of charging sessions",
          modules_referenced: formattedModuleLabels([1, 2]),
          description: "The count of charging events.",
        },
        {
          calculation: "Average of charging session duration",
          modules_referenced: formattedModuleLabels([1, 2]),
          description: "The average session duration.",
        },
        {
          calculation: "Standard deviation of charging session duration",
          modules_referenced: formattedModuleLabels([1, 2]),
          description: "The standard deviation of session duration.",
        },
        {
          calculation: "Median of charging session duration",
          modules_referenced: formattedModuleLabels([1, 2]),
          description: "The median session duration.",
        },
        {
          calculation: "Average peak power per charging session",
          modules_referenced: formattedModuleLabels([1, 2]),
          description: "The average session peak power.",
        },
        {
          calculation: "Cumulative energy dispensed",
          modules_referenced: formattedModuleLabels([1, 2]),
          description: "The sum of session energy.",
        },
      ],
    },
    {
      category: PP_DASHBOARD_SECTION_HEADING_CAPITAL_COSTS,
      exclusions: [
        CalculationExclusions.GENERAL_NON_FED_FUNDED_STATIONS_PORTS,
        CalculationExclusions.GENERAL_DATA_NOT_SUBMITTED_OR_APPROVED,
        CalculationExclusions.GENERAL_DATA_UNREGISTERED_PORTS,
        CalculationExclusions.CAP_COSTS_STATIONS_MISSING_DATA,
        CalculationExclusions.CAP_COSTS_PROPERTY_RESOURCE_COSTS,
      ],
      calculations: [
        {
          calculation: "Average capital cost for NEVI stations",
          modules_referenced: formattedModuleLabels([1, 9]),
          exclusions: [
            CalculationExclusions.CAP_COSTS_NON_NEVI_STATIONS,
          ],
          description: "The sum of total equipment, equipment installation, distribution upgrade and utility connection costs divided by the number of stations funded through the National Electric Vehicle Infrastructure (NEVI) Program.",
        },
        {
          calculation: "X cost to deploy Y ports across Z stations",
          modules_referenced: formattedModuleLabels([1, 9]),
          description: (
            <>
              <div>
                X = The sum of total equipment, equipment installation, distribution upgrade and utility connection costs.
              </div>
              <div className="technical-notes-pp-dashboard-table__calc-desc-div">
                Y = The count of unique ports across stations.
              </div>
              <div className="technical-notes-pp-dashboard-table__calc-desc-div">
                Z = The count of unique stations.
              </div>
            </>
          ),
        },
        {
          calculation: "Federal funding",
          modules_referenced: formattedModuleLabels([1, 9]),
          description: "The sum of federal equipment, equipment installation, distribution upgrade and utility connection costs.",
        },
        {
          calculation: "Non-federal funding",
          modules_referenced: formattedModuleLabels([1, 9]),
          description: "The sum of non-federal equipment, equipment installation, distribution upgrade and utility connection costs.",
        },
      ]
    },
    {
      category: PP_DASHBOARD_SECTION_HEADING_MAINTENANCE_REPAIR_COSTS,
      exclusions: [
        CalculationExclusions.GENERAL_NON_FED_FUNDED_STATIONS_PORTS,
        CalculationExclusions.GENERAL_DATA_NOT_SUBMITTED_OR_APPROVED,
        CalculationExclusions.REPAIR_COSTS_FUTURE_OP_DATA,
        CalculationExclusions.REPAIR_COSTS_CHARGE_AS_SERVICE,
      ],
      calculations: [
        {
          calculation: "Average annual maintenance & repair cost for stations",
          modules_referenced: formattedModuleLabels([1, 5]),
          description:
            "The average monthly maintenance and repair costs across stations where monthly cost is the annual cost reported for that station divided by the number of months it was operational while accruing those costs during the year.",
        },
      ],
    },
  ];

  return (
    <div className="technical-notes-pp-dashboard">
      <GridContainer>
        <DefaultBreadcrumb />
      </GridContainer>
      <div id="TechnicalNotesProgramPerformance">
        <div className="usa-section" style={{ paddingTop: 0 }}>
          <GridContainer>
            <Grid row>
              <Grid col={9}>
                <h1>How are the Program Performance metrics calculated?</h1>
                <p className="technical-notes-pp-dashboard__description">
                  EV-ChART's Program Performance Dashboard tracks EV charging projects funded with Title 23 funds.
                  Non-federally funded stations and ports are excluded from the dashboard. Data is
                  self-reported/approved by direct funding recipients.
                </p>
                <p className="technical-notes-pp-dashboard__description">
                  The table below provides descriptions and associated data modules for each dashboard calculation.
                </p>
                <p className="technical-notes-pp-dashboard__description">
                  Questions?{" "}
                  <a
                    className="evchart-link"
                    href="https://driveelectric.gov/contact/?inquiry=evchart"
                    target="_blank"
                    rel="noreferrer"
                  >
                    Contact EV-ChART
                  </a>
                  .
                </p>
              </Grid>
            </Grid>
            <Grid row>
              <Grid col>
                {tableContent.map(item => (
                  <>
                    <h2>{item.category}</h2>
                    <p className="technical-notes-pp-dashboard-table__calc-exclusions">
                      For all calculations in this section, the following data are excluded:
                      <ul>
                        {item.exclusions.map(exclusion => (
                          <li>{exclusion}</li>
                        ))}
                      </ul>
                    </p>
                    <Table striped fullWidth bordered={false} className="technical-notes-pp-dashboard-table">
                      <thead>
                        <tr>
                          {columnHeaders.map(({ key, label }) => (
                            <th
                              key={key}
                              scope="col"
                              data-testid={key}
                              className={`technical-notes-pp-dashboard-table__th--${key}`}
                            >
                              <div>{label}</div>
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody
                        data-testid="technicalNotesProgramPerformanceTable"
                        className="technical-notes-pp-dashboard-table__tbody"
                      >
                        {item.calculations.map((item, index) => (
                          <tr data-testid="technicalNotesProgramPerformanceRow" key={index}>
                            <td>{item.calculation}</td>
                            <td>{item.modules_referenced}</td>
                            <td>
                              <div>{item.description}</div>
                              {item.exclusions && (
                                <div className="technical-notes-pp-dashboard-table__calc-desc-div technical-notes-pp-dashboard-table__calc-exclusions">
                                  The following data are excluded:
                                  <ul>
                                    {item.exclusions.map(exclusion => (
                                      <li>{exclusion}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  </>
                ))}
              </Grid>
            </Grid>
          </GridContainer>
        </div>
      </div>
    </div>
  );
}

export default TechnicalNotesProgramPerformance;
