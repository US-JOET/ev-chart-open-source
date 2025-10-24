export interface StationInfo {
  nickname: string;
  station_id: string;
  station_uuid: string;
  removeable: boolean;
  authorized_subrecipients: string;
  dr_name: string;
  status: string;
  federally_funded: string;
}

export interface StationOption {
  station_uuid: string;
  station_id: string;
  nickname: string;
}

export interface PortsInfo {
  port_uuid?: string;
  port_id: string;
  port_type: string;
}

export interface StationDetailsViewOnly {
  station_uuid: string;
  address: string;
  city: string;
  project_type: string;
  station_id: string;
  latitude: string;
  longitude: string;
  nickname: string;
  num_fed_funded_ports: string;
  num_non_fed_funded_ports: string;
  state: string;
  status: string;
  network_provider: string;
  operational_date: string;
  AFC: number;
  NEVI: number;
  CFI: number;
  EVC_RAA: number;
  CMAQ: number;
  CRP: number;
  OTHER: number;
  authorized_subrecipients: string[];
  zip: string;
  zip_extended: string;
  fed_funded_ports: PortsInfo[];
  non_fed_funded_ports: PortsInfo[];
}

export interface StationAddNew {
  address: string;
  city: string;
  project_type: string;
  station_id: string;
  latitude: string;
  longitude: string;
  nickname: string;
  federally_funded: boolean | null;
  num_fed_funded_ports: number | null;
  num_non_fed_funded_ports: number | null;
  state: string;
  status: string;
  network_provider: string;
  operational_date: string;
  NEVI: number;
  CFI: number;
  EVC_RAA: number;
  CMAQ: number;
  CRP: number;
  OTHER: number;
  AFC: number | undefined;
  authorized_subrecipients: string[];
  zip: string;
  zip_extended: string;
  fed_funded_ports: PortsInfo[];
  non_fed_funded_ports: PortsInfo[];
  dr_id: string;
}

export interface EditedStationValues {
  address?: string;
  city?: string;
  project_type?: string;
  station_id?: string;
  station_uuid?: string;
  latitude?: string;
  longitude?: string;
  nickname?: string;
  federally_funded?: boolean | null;
  num_fed_funded_ports?: number;
  num_non_fed_funded_ports?: number | null;
  state?: string;
  status?: string;
  network_provider?: string;
  NEVI?: number;
  CFI?: number;
  EVC_RAA?: number;
  CMAQ?: number;
  CRP?: number;
  OTHER?: number;
  AFC?: number;
  authorized_subrecipients?: string[];
  srs_removed?: string[];
  srs_added?: string[];
  zip?: string;
  zip_extended?: string;
  fed_funded_ports?: PortsInfo[];
  non_fed_funded_ports?: PortsInfo[];
  ports_removed?: string[];
}
export interface CharacterMapping {
  [key: string]: number;
}
