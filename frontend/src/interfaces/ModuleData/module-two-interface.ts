export interface ModuleTwoHeaders {
  station_id: string;
  port_id: string;
  charger_id: string;
  session_id: string;
  connector_id: string;
  // "provider_id": string,
  session_start: string;
  session_end: string;
  session_error: string;
  error_other: string;
  energy_kwh: string;
  power_kw: string;
  payment_method: string;
  payment_other: string;
}

export interface ModuleTwoDatum {
  station_id: string;
  port_id: string;
  charger_id: string;
  session_id: string;
  connector_id: string;
  // "provider_id": string,
  session_start: string;
  session_end: string;
  session_error: string;
  error_other: string;
  energy_kwh: number;
  power_kw: number;
  payment_method: string;
  payment_other: string;
}

export interface ModuleTwoData {
  moduleId: string;
  leftHeaders: Array<string>;
  rightHeaders: Array<string>;
  headerText: ModuleTwoHeaders;
  data: Array<ModuleTwoDatum>;
}
