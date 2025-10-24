import { describe, it, expect, vi } from "vitest";

import {
  getSubmitModuleSubtext,
  getApprovedRejectedModuleSubtext,
} from "../../../src/containers/ModuleData/ModuleData";
import * as utils from "../../../src/utils/getJWTInfo";

vi.spyOn(utils, "getScope");

const getSubmitModuleSubtextTestCases = [
  {
    scope: "sub-recipient",
    stateInfo: {
      directRecipient: "Pennsylvania DOT",
      moduleType: "One-Time",
      moduleName: "Module 9: Capital and Installation Costs",
      moduleYear: "2023",
    },
    expected:
      "Pennsylvania DOT will be notified by email that Module 9: Capital and Installation Costs requires their approval for final submission.",
  },
  {
    scope: "sub-recipient",
    stateInfo: {
      directRecipient: "Pennsylvania DOT",
      moduleType: "Annual",
      moduleName: "Module 5: Maintenance Costs",
      moduleYear: "2023",
    },
    expected:
      "Pennsylvania DOT will be notified by email that Module 5: Maintenance Costs for 2023 requires their approval for final submission.",
  },
  {
    scope: "sub-recipient",
    stateInfo: {
      directRecipient: "Pennsylvania DOT",
      moduleType: "Quarter 3 (Jul-Sep)",
      moduleName: "Module 2: Charging Sessions",
      moduleYear: "2023",
    },
    expected:
      "Pennsylvania DOT will be notified by email that Module 2: Charging Sessions for Quarter 3 (Jul-Sep) requires their approval for final submission.",
  },
  {
    scope: "direct-recipient",
    stateInfo: {
      directRecipient: "Pennsylvania DOT",
      moduleType: "One-Time",
      moduleName: "Module 9: Capital and Installation Costs",
      moduleYear: "2023",
    },
    expected:
      "You successfully submitted Module 9: Capital and Installation Costs, a one-time submission, for Pennsylvania DOT. No further action is required.",
  },
  {
    scope: "direct-recipient",
    stateInfo: {
      directRecipient: "Pennsylvania DOT",
      moduleType: "Annual",
      moduleName: "Module 5: Maintenance Costs",
      moduleYear: "2023",
    },
    expected:
      "You successfully submitted Module 5: Maintenance Costs for 2023 for Pennsylvania DOT. No further action is required.",
  },
  {
    scope: "direct-recipient",
    stateInfo: {
      directRecipient: "Pennsylvania DOT",
      moduleType: "Quarter 3 (Jul-Sep)",
      moduleName: "Module 2: Charging Sessions",
      moduleYear: "2023",
    },
    expected:
      "You successfully submitted Module 2: Charging Sessions for Quarter 3 (Jul-Sep) for Pennsylvania DOT. No further action is required.",
  },
];

const getApprovedRejectedModuleSubtextTestCases = [
  {
    approve: true,
    stateInfo: {
      directRecipient: "Pennsylvania DOT",
      moduleType: "One-Time",
      moduleName: "Module 9: Capital and Installation Costs",
      moduleYear: "2023",
    },
    expected:
      "The subrecipient/contractor will be notified by email of the approval of Module 9: Capital and Installation Costs, a one-time submission.",
  },
  {
    approve: true,
    stateInfo: {
      directRecipient: "Pennsylvania DOT",
      moduleType: "Annual",
      moduleName: "Module 5: Maintenance Costs",
      moduleYear: "2023",
    },
    expected:
      "The subrecipient/contractor will be notified by email of the approval of Module 5: Maintenance Costs for 2023.",
  },
  {
    approve: true,
    stateInfo: {
      directRecipient: "Pennsylvania DOT",
      moduleType: "Quarter 3 (Jul-Sep)",
      moduleName: "Module 2: Charging Sessions",
      moduleYear: "2023",
    },
    expected:
      "The subrecipient/contractor will be notified by email of the approval of Module 2: Charging Sessions for Quarter 3 (Jul-Sep), 2023.",
  },
  {
    approve: false,
    stateInfo: {
      directRecipient: "Pennsylvania DOT",
      moduleType: "One-Time",
      moduleName: "Module 9: Capital and Installation Costs",
      moduleYear: "2023",
    },
    expected:
      "The subrecipient/contractor will be notified by email of the rejection of Module 9: Capital and Installation Costs, a one-time submission.",
  },
  {
    approve: false,
    stateInfo: {
      directRecipient: "Pennsylvania DOT",
      moduleType: "Annual",
      moduleName: "Module 5: Maintenance Costs",
      moduleYear: "2023",
    },
    expected:
      "The subrecipient/contractor will be notified by email of the rejection of Module 5: Maintenance Costs for 2023.",
  },
  {
    approve: false,
    stateInfo: {
      directRecipient: "Pennsylvania DOT",
      moduleType: "Quarter 3 (Jul-Sep)",
      moduleName: "Module 2: Charging Sessions",
      moduleYear: "2023",
    },
    expected:
      "The subrecipient/contractor will be notified by email of the rejection of Module 2: Charging Sessions for Quarter 3 (Jul-Sep), 2023.",
  },
];

describe("getSubmitModuleSubtext", () => {
  it.each(getSubmitModuleSubtextTestCases)(
    "returns the correct subtext for scope: $scope and stateInfo: $stateInfo",
    ({ scope, stateInfo, expected }) => {
      vi.spyOn(utils, "getScope").mockReturnValue(scope);
      const result = getSubmitModuleSubtext(stateInfo);
      expect(result).toBe(expected);
    },
  );
});

describe("getApprovedRejectedModuleSubtext", () => {
  it.each(getApprovedRejectedModuleSubtextTestCases)(
    "returns the correct subtext for stateInfo: $stateInfo",
    ({ approve, stateInfo, expected }) => {
      const result = getApprovedRejectedModuleSubtext(stateInfo, approve);
      expect(result).toBe(expected);
    },
  );
});
