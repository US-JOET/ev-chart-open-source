export interface ModuleFourHeaders {
  station_id: string;
  port_id: string;
  outage_id: string;
  outage_duration: string;
  excluded_outage: string;
  excluded_outage_reason: string;
  excluded_outage_notes: string;
}

export interface ModuleFourDatum {
  station_id: string;
  port_id: string;
  outage_id: string;
  outage_duration: number;
  excluded_outage: string;
  excluded_outage_reason: string;
  excluded_outage_notes: string;
}

export interface ModuleFourData {
  moduleId: string;
  leftHeaders: Array<string>;
  rightHeaders: Array<string>;
  headerText: ModuleFourHeaders;
  data: Array<ModuleFourDatum>;
}
