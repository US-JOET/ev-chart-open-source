export interface ModuleNineHeaders {
  station_id: string;
  station_upgrade: string;
  real_property_acq_date: string;
  real_property_acq_type: string;
  real_property_cost_total: string;
  real_property_cost_federal: string;
  equipment_acq_date: string;
  equipment_acq_type: string;
  equipment_cost_total: string;
  equipment_cost_federal: string;
  equipment_install_date: string;
  equipment_install_cost_total: string;
  equipment_install_cost_federal: string;
  equipment_install_cost_elec: string;
  equipment_install_cost_const: string;
  equipment_install_cost_labor: string;
  equipment_install_cost_other: string;
  der_acq_type: string;
  der_cost_total: string;
  der_cost_federal: string;
  der_install_cost_total: string;
  der_install_cost_federal: string;
  dist_sys_cost_total: string;
  dist_sys_cost_federal: string;
  service_cost_total: string;
  service_cost_federal: string;
}

export interface ModuleNineDatum {
  station_id: string;
  station_upgrade: string;
  real_property_acq_date: string;
  real_property_acq_type: string;
  real_property_cost_total: number;
  real_property_cost_federal: number;
  equipment_acq_date: string;
  equipment_acq_type: string;
  equipment_cost_total: number;
  equipment_cost_federal: number;
  equipment_install_date: string;
  equipment_install_cost_total: number;
  equipment_install_cost_federal: number;
  equipment_install_cost_elec: number;
  equipment_install_cost_const: number;
  equipment_install_cost_labor: number;
  equipment_install_cost_other: number;
  der_acq_type: string;
  der_cost_total: string;
  der_cost_federal: string;
  der_install_cost_total: string;
  der_install_cost_federal: string;
  dist_sys_cost_total: string;
  dist_sys_cost_federal : string;
  service_cost_total: string;
  service_cost_federal: string;
}

export interface ModuleNineData {
  moduleId: string;
  leftHeaders: Array<string>;
  rightHeaders: Array<string>;
  headerText: ModuleNineHeaders;
  data: Array<ModuleNineDatum>;
}
