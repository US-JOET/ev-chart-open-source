export interface ModuleSevenHeaders {
  station_id: string;
  program_report_year: string;
  opportunity_program: string;
  program_descript: string;
}

export interface ModuleSevenDatum {
  station_id: string;
  program_report_year: number;
  opportunity_program: string;
  program_descript: string;
}

export interface ModuleSevenData {
  moduleId: string;
  leftHeaders: Array<string>;
  rightHeaders: Array<string>;
  headerText: ModuleSevenHeaders;
  data: Array<ModuleSevenDatum>;
}
