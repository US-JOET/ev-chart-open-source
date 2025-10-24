export interface ModuleThreeHeaders {
  station_id: string;
  port_id: string;
  uptime_reporting_start: string;
  uptime_reporting_end: string;
  uptime: string;
  total_outage: string;
  total_outage_excl: string;
}

export interface ModuleThreeDatum {
  station_id: string;
  port_id: string;
  uptime_reporting_start: string;
  uptime_reporting_end: string;
  uptime: number;
  total_outage: number;
  total_outage_excl: number;
}

export interface ModuleThreeData {
  moduleId: string;
  leftHeaders: Array<string>;
  rightHeaders: Array<string>;
  headerText: ModuleThreeHeaders;
  data: Array<ModuleThreeDatum>;
}
