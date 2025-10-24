import { format } from "date-fns";

export const PP_DASHBOARD_SECTION_HEADING_NETWORK_SIZE = "Federally Funded Network Size";
export const PP_DASHBOARD_SECTION_HEADING_RELIABILITY = "Reliability";
export const PP_DASHBOARD_SECTION_HEADING_CAPITAL_COSTS = "Capital Costs";
export const PP_DASHBOARD_SECTION_HEADING_MAINTENANCE_REPAIR_COSTS = "Maintenance & Repair Costs";
export const PP_DASHBOARD_SECTION_HEADING_ENERGY_USAGE = "Energy Usage";

export const TODAY = new Date();

// Variable for dashboard updated time
export const getDashboardUpdatedTime = () => {
  // Set time
  const dashboardUpdatedTime = format(TODAY, "MM/dd/yyyy 'at' h:mm a");
  return dashboardUpdatedTime;
};

// Variable for dashboard updated day
export const getDashboardUpdatedDay = () => {
  // Set time
  const dashboardUpdatedDay = format(TODAY, "MM/dd/yyyy");
  return dashboardUpdatedDay;
};
