export interface ModuleEightHeaders {
  station_id: string;
  der_upgrade: string;
  der_onsite: string;
  der_type: string;
  der_type_other: string;
  der_kw: string;
  der_kwh: string;
}

export interface ModuleEightDatum {
  station_id: string;
  der_upgrade: string;
  der_onsite: string;
  der_type: string;
  der_type_other: string;
  der_kw: number;
  der_kwh: number;
}

export interface ModuleEightData {
  moduleId: string;
  leftHeaders: Array<string>;
  rightHeaders: Array<string>;
  headerText: ModuleEightHeaders;
  data: Array<ModuleEightDatum>;
}
