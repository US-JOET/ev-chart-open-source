export function valideKpiMagnitude(value: number | null): string | null {
  if (value == null) {
    return value;
  }
  if (value < 10) {
    return `${parseFloat(value.toFixed(2))}`;
  }
  if (value < 100) {
    return `${parseFloat(value.toFixed(1))}`;
  }
  if (value < 1_000) {
    return `${parseFloat(value.toFixed(0))}`;
  }
  if (value < 10_000) {
    const scaledNumber = value / 1_000;
    return `${parseFloat(scaledNumber.toFixed(2))} K`;
  }
  if (value < 100_000) {
    const scaledNumber = value / 1_000;
    return `${parseFloat(scaledNumber.toFixed(1))} K`;
  }
  if (value < 1_000_000) {
    const scaledNumber = value / 1_000;
    return `${parseFloat(scaledNumber.toFixed(0))} K`;
  }
  if (value < 10_000_000) {
    const scaledNumber = value / 1_000_000;
    return `${parseFloat(scaledNumber.toFixed(2))} M`;
  }
  if (value < 100_000_000) {
    const scaledNumber = value / 1_000_000;
    return `${parseFloat(scaledNumber.toFixed(1))} M`;
  }
  if (value < 1_000_000_000) {
    const scaledNumber = value / 1_000_000;
    return `${parseFloat(scaledNumber.toFixed(0))} M`;
  }
  const scaledNumber = value / 1_000_000_000;
  return `${parseFloat(scaledNumber.toFixed(2))} G`;
}

export function valideKpiMagnitudeEnergyMetrics(value: number | null): string | null {
  if (value == null) {
    return value;
  }
  if (value < 10) {
    return `${parseFloat(value.toFixed(2))} k`;
  }
  if (value < 100) {
    return `${parseFloat(value.toFixed(1))} k`;
  }
  if (value < 1_000) {
    return `${parseFloat(value.toFixed(0))} k`;
  }
  if (value < 10_000) {
    const scaledNumber = value / 1_000;
    return `${parseFloat(scaledNumber.toFixed(2))} M`;
  }
  if (value < 100_000) {
    const scaledNumber = value / 1_000;
    return `${parseFloat(scaledNumber.toFixed(1))} M`;
  }
  if (value < 1_000_000) {
    const scaledNumber = value / 1_000;
    return `${parseFloat(scaledNumber.toFixed(0))} M`;
  }
  if (value < 10_000_000) {
    const scaledNumber = value / 1_000_000;
    return `${parseFloat(scaledNumber.toFixed(2))} G`;
  }
  if (value < 100_000_000) {
    const scaledNumber = value / 1_000_000;
    return `${parseFloat(scaledNumber.toFixed(1))} G`;
  }
  if (value < 1_000_000_000) {
    const scaledNumber = value / 1_000_000;
    return `${parseFloat(scaledNumber.toFixed(0))} G`;
  }
  const scaledNumber = value / 1_000_000_000;
  return `${parseFloat(scaledNumber.toFixed(2))} T`;
}

export function convertNumberToBaseUnits(value: number, unit: string): number {
  const siPrefixes = [
    { prefix: "T", factor: 1e12 },
    { prefix: "G", factor: 1e9 },
    { prefix: "M", factor: 1e6 },
    { prefix: "k", factor: 1e3 },
    { prefix: "h", factor: 1e2 },
    { prefix: "da", factor: 1e1 },
    { prefix: "d", factor: 1e-1 },
    { prefix: "c", factor: 1e-2 },
    { prefix: "m", factor: 1e-3 },
    { prefix: "µ", factor: 1e-6 },
    { prefix: "n", factor: 1e-9 },
    { prefix: "p", factor: 1e-12 },
  ];
  const prefix = siPrefixes.find((siPrefix) => unit.startsWith(siPrefix.prefix));
  if (prefix) {
    return value * prefix.factor;
  } else {
    // No prefix, already in base units
    return value;
  }
}

export function formatKpiMagnitude(value: number | null, metricType?: string, unit?: string): string {
  if (value && unit) {
    value = convertNumberToBaseUnits(value, unit);
  }

  let kpiMagnitude;
  switch (metricType) {
    case "energy":
      kpiMagnitude = valideKpiMagnitudeEnergyMetrics(value);
      break;
    case "percentage": {
      const decimalToPercentage = value ? value * 100 : value;
      kpiMagnitude = valideKpiMagnitude(decimalToPercentage);
      break;
    }
    default:
      kpiMagnitude = valideKpiMagnitude(value);
  }

  if (kpiMagnitude == null) {
    return metricType === "energy" ? "-- k" : "--";
  }
  return kpiMagnitude;
}
