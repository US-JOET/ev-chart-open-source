export interface ModuleFiveHeaders {
  station_id: string;
  maintenance_report_start: string;
  maintenance_report_end: string;
  caas: string;
  maintenance_cost_total: string;
  maintenance_cost_federal: string;
}

export interface ModuleFiveDatum {
  station_id: string;
  maintenance_report_start: string;
  maintenance_report_end: string;
  caas: string;
  maintenance_cost_total: number;
  maintenance_cost_federal: number;
}

export interface ModuleFiveData {
  moduleId: string;
  leftHeaders: Array<string>;
  rightHeaders: Array<string>;
  headerText: ModuleFiveHeaders;
  data: Array<ModuleFiveDatum>;
}
