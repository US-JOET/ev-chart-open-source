export interface NetworkSizeInterface {
  totalStations: string;
  portsAtStations: string;
  l2Ports: string;
  dcfcPorts: string;
  undefinedPorts: string;
}

export interface ReliabilityInterface {
  numberPortsReqMet: string;
  totalPortsReqMet: string;
  percentagePortsReqMet: string;
  percentagePortsReqNotMet: string;
  avgTime: string;
}

export interface CapitalCostsInterface {
  stationCapitalCost: string;
  totalCost: string;
  numberPorts: string;
  numberStations: string;
  federalCost: string;
  nonfederalCost: string;
}

export interface EnergyUsageInterface {
  totalChargingSessions: string;
  avgChargingDuration: string;
  stdevChargingSession: string;
  medianChargingSession: string;
  cumulativeEnergy: string;
  avgChargingPower: string;
}
