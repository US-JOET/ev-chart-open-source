export enum ModuleName {
  Module1 = "Station Location",
  Module2 = "Charging Sessions",
  Module3 = "Uptime",
  Module4 = "Outages",
  Module5 = "Maintenance Costs",
  Module6 = "Station Operator Identity",
  Module7 = "Station Operator Program",
  Module8 = "DER Information",
  Module9 = "Capital and Installation Costs",
}

export const ModuleNameMap: Record<number, ModuleName> = {
  1: ModuleName.Module1,
  2: ModuleName.Module2,
  3: ModuleName.Module3,
  4: ModuleName.Module4,
  5: ModuleName.Module5,
  6: ModuleName.Module6,
  7: ModuleName.Module7,
  8: ModuleName.Module8,
  9: ModuleName.Module9,
};

export const getModuleNameById = (moduleId: number): ModuleName => ModuleNameMap[moduleId];

export const formatModuleNameLabel = (moduleId: number): string => {
  return `Module ${moduleId} (${getModuleNameById(moduleId)})`;
};
