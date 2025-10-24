export interface ModuleSixHeaders {
  station_id: string;
  operator_name: string;
  operator_address: string;
  operator_city: string;
  operator_state: string;
  operator_zip: string;
  operator_zip_extended: string;
}

export interface ModuleSixDatum {
  station_id: string;
  operator_name: string;
  operator_address: string;
  operator_city: string;
  operator_state: string;
  operator_zip: string;
  operator_zip_extended: string;
}

export interface ModuleSixData {
  moduleId: string;
  leftHeaders: Array<string>;
  rightHeaders: Array<string>;
  headerText: ModuleSixHeaders;
  data: Array<ModuleSixDatum>;
}
