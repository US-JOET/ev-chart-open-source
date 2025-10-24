import { describe, expect, test } from "vitest";
import {
  convertNumberToBaseUnits,
  formatKpiMagnitude,
  valideKpiMagnitude,
  valideKpiMagnitudeEnergyMetrics,
} from "./kpi-magnitude";

describe("valideKpiMagnitude", () => {
  test("null", () => {
    expect(valideKpiMagnitude(null)).toBe(null);
  });

  test("no units 1.67", () => {
    expect(valideKpiMagnitude(1.67)).toBe("1.67");
  });

  test("no units 10", () => {
    expect(valideKpiMagnitude(10)).toBe("10");
  });

  test("no units 12.01", () => {
    expect(valideKpiMagnitude(12.01)).toBe("12");
  });

  test("no units 101", () => {
    expect(valideKpiMagnitude(101)).toBe("101");
  });

  test("no units 16.78", () => {
    expect(valideKpiMagnitude(16.78)).toBe("16.8");
  });

  test("no units 999.1", () => {
    expect(valideKpiMagnitude(999.1)).toBe("999");
  });

  test("display with K 1,000", () => {
    expect(valideKpiMagnitude(1_000)).toBe("1 K");
  });

  test("display with K 1,234", () => {
    expect(valideKpiMagnitude(1_234)).toBe("1.23 K");
  });

  test("display with K 12,345", () => {
    expect(valideKpiMagnitude(12_345)).toBe("12.3 K");
  });

  test("display with K 123,123", () => {
    expect(valideKpiMagnitude(123_123)).toBe("123 K");
  });

  test("display with K 999,190", () => {
    expect(valideKpiMagnitude(999_190)).toBe("999 K");
  });

  test("display with M 1,004,980", () => {
    expect(valideKpiMagnitude(1_004_980)).toBe("1 M");
  });

  test("display with M 1,234,456", () => {
    expect(valideKpiMagnitude(1_234_456)).toBe("1.23 M");
  });

  test("display with M 12,345,678", () => {
    expect(valideKpiMagnitude(12_345_678)).toBe("12.3 M");
  });

  test("display with M 123,456,789", () => {
    expect(valideKpiMagnitude(123_456_789)).toBe("123 M");
  });

  test("display with B 1,234,567,890", () => {
    expect(valideKpiMagnitude(1_234_567_890)).toBe("1.23 G");
  });
});

describe("valideKpiMagnitudeEnergyMetrics", () => {
  test("null", () => {
    expect(valideKpiMagnitudeEnergyMetrics(null)).toBe(null);
  });

  test("display with k 0k", () => {
    expect(valideKpiMagnitudeEnergyMetrics(0)).toBe("0 k");
  });

  test("display with k 1.67k", () => {
    expect(valideKpiMagnitudeEnergyMetrics(1.67)).toBe("1.67 k");
  });

  test("display with k 10k", () => {
    expect(valideKpiMagnitudeEnergyMetrics(10)).toBe("10 k");
  });

  test("display with k 12.01k", () => {
    expect(valideKpiMagnitudeEnergyMetrics(12.01)).toBe("12 k");
  });

  test("display with k 101k", () => {
    expect(valideKpiMagnitudeEnergyMetrics(101)).toBe("101 k");
  });

  test("display with k 16.78k", () => {
    expect(valideKpiMagnitudeEnergyMetrics(16.78)).toBe("16.8 k");
  });

  test("display with k 999.1k", () => {
    expect(valideKpiMagnitudeEnergyMetrics(999.1)).toBe("999 k");
  });

  test("display with M 1,000k", () => {
    expect(valideKpiMagnitudeEnergyMetrics(1_000)).toBe("1 M");
  });

  test("display with M 1,234k", () => {
    expect(valideKpiMagnitudeEnergyMetrics(1_234)).toBe("1.23 M");
  });

  test("display with M 12,345k", () => {
    expect(valideKpiMagnitudeEnergyMetrics(12_345)).toBe("12.3 M");
  });

  test("display with M 123,123k", () => {
    expect(valideKpiMagnitudeEnergyMetrics(123_123)).toBe("123 M");
  });

  test("display with M 999,190k", () => {
    expect(valideKpiMagnitudeEnergyMetrics(999_190)).toBe("999 M");
  });

  test("display with G 1,004,980k", () => {
    expect(valideKpiMagnitudeEnergyMetrics(1_004_980)).toBe("1 G");
  });

  test("display with G 1,234,456k", () => {
    expect(valideKpiMagnitudeEnergyMetrics(1_234_456)).toBe("1.23 G");
  });

  test("display with G 12,345,678k", () => {
    expect(valideKpiMagnitudeEnergyMetrics(12_345_678)).toBe("12.3 G");
  });

  test("display with G 123,456,789k", () => {
    expect(valideKpiMagnitudeEnergyMetrics(123_456_789)).toBe("123 G");
  });

  test("display with T 1,234,567,890k", () => {
    expect(valideKpiMagnitudeEnergyMetrics(1_234_567_890)).toBe("1.23 T");
  });
});

describe("convertNumberToBaseUnits", () => {
  test("1.67 mm", () => {
    expect(convertNumberToBaseUnits(1.67, "mm")).toBe(0.00167);
  });

  test("1.67 no units", () => {
    expect(convertNumberToBaseUnits(1.67, "")).toBe(1.67);
  });

  test("1.67 base units", () => {
    expect(convertNumberToBaseUnits(1.67, "g")).toBe(1.67);
  });

  test("1.67 kWh", () => {
    expect(convertNumberToBaseUnits(1.67, "kWh")).toBe(1_670);
  });

  test("1.67 MWh", () => {
    expect(convertNumberToBaseUnits(1.67, "MWh")).toBe(1_670_000);
  });
});

describe("formatKpiMagnitude", () => {
  test("formatKpiMagnitude null value", () => {
    expect(formatKpiMagnitude(null)).toBe("--");
  });

  test("formatKpiMagnitude 0 value", () => {
    const value = 0;
    const result = formatKpiMagnitude(value);
    expect(result).toBe("0");
  });

  test("formatKpiMagnitude non-null value", () => {
    const value = 123_456_789;
    expect(formatKpiMagnitude(value)).toBe(valideKpiMagnitude(value));
    expect(formatKpiMagnitude(value)).toBeTypeOf("string");
  });

  test("formatKpiMagnitude display with K 1.67kW", () => {
    expect(formatKpiMagnitude(1.67, undefined, "kWh")).toBe("1.67 K");
  });

  test("formatKpiMagnitude display with M 1,000kW", () => {
    expect(formatKpiMagnitude(1_000, undefined, "kWh")).toBe("1 M");
  });

  test("formatKpiMagnitude energy metrics null value", () => {
    expect(formatKpiMagnitude(null, "energy")).toBe("-- k");
  });

  test("formatKpiMagnitude energy metrics 0k", () => {
    expect(formatKpiMagnitude(0, "energy")).toBe("0 k");
  });

  test("formatKpiMagnitude energy metrics 0.167k", () => {
    expect(formatKpiMagnitude(0.167, "energy")).toBe("0.17 k");
  });

  test("formatKpiMagnitude energy metrics 1.67k", () => {
    expect(formatKpiMagnitude(1.67, "energy")).toBe("1.67 k");
  });

  test("formatKpiMagnitude energy metrics 1,000k", () => {
    expect(formatKpiMagnitude(1_000, "energy")).toBe("1 M");
  });

  test("formatKpiMagnitude percentage metrics 0.32", () => {
    expect(formatKpiMagnitude(0.32, "percentage")).toBe("32");
  });

  test("formatKpiMagnitude percentage metrics 0.05", () => {
    expect(formatKpiMagnitude(0.05, "percentage")).toBe("5");
  });

  test("formatKpiMagnitude percentage metrics 0.051", () => {
    expect(formatKpiMagnitude(0.051, "percentage")).toBe("5.1");
  });

  test("formatKpiMagnitude percentage metrics 0.5", () => {
    expect(formatKpiMagnitude(0.5, "percentage")).toBe("50");
  });
});
