import { describe, expect, it, vi, beforeEach } from "vitest";
import moment from "moment";

import {
  AnnualOneTimeHeading,
  DRAnnualOneTimeText,
  DRQuarterFourText,
  DRQuarterOneText,
  DRQuarterThreeText,
  DRQuarterTwoText,
  getDueDateAlert,
  Quarter1Heading,
  Quarter2Heading,
  Quarter3Heading,
  Quarter4Heading,
  SRAnnualOneTimeText,
  SRQuarterFourText,
  SRQuarterOneText,
  SRQuarterThreeText,
  SRQuarterTwoText,
} from "./DueDateAlert";
import * as authFunctions from "../../utils/authFunctions";

//Mock isDRUser() function
vi.mock("../../utils/authFunctions", () => ({
  isDRUser: vi.fn(() => false),
}));

describe("getDueDateAlert", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  describe("Annual & One-Time Data (due March 1)", () => {
    it("shows dr alert at the beginning of the window (Feb 1)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(true);
      const today = moment("2025-02-01");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(AnnualOneTimeHeading);
      expect(result.text).toBe(DRAnnualOneTimeText);
    });
    it("shows dr alert in middle of the window (Feb 12)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(true);
      const today = moment("2025-02-12");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(AnnualOneTimeHeading);
      expect(result.text).toBe(DRAnnualOneTimeText);
    });
    it("shows dr alert last day of the window (Mar 1)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(true);
      const today = moment("2025-03-01");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(AnnualOneTimeHeading);
      expect(result.text).toBe(DRAnnualOneTimeText);
    });
    it("shows sr alert at the beginning of the window (Feb 1)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(false);
      const today = moment("2025-02-01");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(AnnualOneTimeHeading);
      expect(result.text).toBe(SRAnnualOneTimeText);
    });
    it("shows sr alert in middle of the window (Feb 12)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(false);
      const today = moment("2025-02-12");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(AnnualOneTimeHeading);
      expect(result.text).toBe(SRAnnualOneTimeText);
    });
    it("shows sr alert last day of the window (Mar 1)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(false);
      const today = moment("2025-03-01");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(AnnualOneTimeHeading);
      expect(result.text).toBe(SRAnnualOneTimeText);
    });
    it("alert does not show past mar 1", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(false);
      const today = moment("2025-03-02");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(false);
    });
  });

  describe("Quarter 1 (due Apr 30)", () => {
    it("shows dr alert at the beginning of the window (Mar 31)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(true);
      const today = moment("2025-03-31");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(Quarter1Heading);
      expect(result.text).toBe(DRQuarterOneText);
    });
    it("shows dr alert in middle of the window (Apr 15)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(true);
      const today = moment("2025-04-15");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(Quarter1Heading);
      expect(result.text).toBe(DRQuarterOneText);
    });
    it("shows dr alert last day of the window (Apr 30)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(true);
      const today = moment("2025-04-30");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(Quarter1Heading);
      expect(result.text).toBe(DRQuarterOneText);
    });
    it("shows sr alert at the beginning of the window (Mar 31)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(false);
      const today = moment("2025-03-31");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(Quarter1Heading);
      expect(result.text).toBe(SRQuarterOneText);
    });
    it("shows sr alert in middle of the window (Apr 15)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(false);
      const today = moment("2025-04-15");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(Quarter1Heading);
      expect(result.text).toBe(SRQuarterOneText);
    });
    it("shows sr alert last day of the window (Apr 30)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(false);
      const today = moment("2025-04-30");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(Quarter1Heading);
      expect(result.text).toBe(SRQuarterOneText);
    });
    it("alert does not show past Apr 30", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(false);
      const today = moment("2025-05-01");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(false);
    });
  });

  describe("Quarter 2 (due Apr 30)", () => {
    it("shows dr alert at the beginning of the window (June 30)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(true);
      const today = moment("2025-06-30");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(Quarter2Heading);
      expect(result.text).toBe(DRQuarterTwoText);
    });
    it("shows dr alert in middle of the window (Jul 15)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(true);
      const today = moment("2025-07-15");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(Quarter2Heading);
      expect(result.text).toBe(DRQuarterTwoText);
    });
    it("shows dr alert last day of the window (Jul 31)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(true);
      const today = moment("2025-07-31");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(Quarter2Heading);
      expect(result.text).toBe(DRQuarterTwoText);
    });
    it("shows sr alert at the beginning of the window (June 30)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(false);
      const today = moment("2025-06-30");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(Quarter2Heading);
      expect(result.text).toBe(SRQuarterTwoText);
    });
    it("shows sr alert in middle of the window (Jul 15)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(false);
      const today = moment("2025-07-15");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(Quarter2Heading);
      expect(result.text).toBe(SRQuarterTwoText);
    });
    it("shows sr alert last day of the window (Jul 31)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(false);
      const today = moment("2025-07-31");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(Quarter2Heading);
      expect(result.text).toBe(SRQuarterTwoText);
    });
    it("alert does not show past Jul 31", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(false);
      const today = moment("2025-08-01");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(false);
    });
  });

  describe("Quarter 3 (due Oct 31)", () => {
    it("shows dr alert at the beginning of the window (Sep 30)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(true);
      const today = moment("2025-09-30");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(Quarter3Heading);
      expect(result.text).toBe(DRQuarterThreeText);
    });
    it("shows dr alert in middle of the window (Oct 15)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(true);
      const today = moment("2025-10-15");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(Quarter3Heading);
      expect(result.text).toBe(DRQuarterThreeText);
    });
    it("shows dr alert last day of the window (Oct 31)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(true);
      const today = moment("2025-10-31");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(Quarter3Heading);
      expect(result.text).toBe(DRQuarterThreeText);
    });
    it("shows sr alert at the beginning of the window (Sep 30)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(false);
      const today = moment("2025-09-30");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(Quarter3Heading);
      expect(result.text).toBe(SRQuarterThreeText);
    });
    it("shows sr alert in middle of the window (Oct 15)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(false);
      const today = moment("2025-10-15");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(Quarter3Heading);
      expect(result.text).toBe(SRQuarterThreeText);
    });
    it("shows sr alert last day of the window (Oct 31)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(false);
      const today = moment("2025-10-31");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(Quarter3Heading);
      expect(result.text).toBe(SRQuarterThreeText);
    });

    it("alert does not show past Oct 31", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(false);
      const today = moment("2025-11-01");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(false);
    });
  });

  describe("Quarter 4 (due Jan 31)", () => {
    it("shows dr alert at the beginning of the window (Jan 1)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(true);
      const today = moment("2025-01-01");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(Quarter4Heading);
      expect(result.text).toBe(DRQuarterFourText);
    });
    it("shows dr alert in middle of the window (Jan 15)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(true);
      const today = moment("2025-01-15");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(Quarter4Heading);
      expect(result.text).toBe(DRQuarterFourText);
    });
    it("shows dr alert last day of the window (Jan 31)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(true);
      const today = moment("2025-01-31");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(Quarter4Heading);
      expect(result.text).toBe(DRQuarterFourText);
    });
    it("shows sr alert at the beginning of the window (Jan 1)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(false);
      const today = moment("2025-01-01");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(Quarter4Heading);
      expect(result.text).toBe(SRQuarterFourText);
    });
    it("shows sr alert in middle of the window (Jan 15)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(false);
      const today = moment("2025-01-15");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(Quarter4Heading);
      expect(result.text).toBe(SRQuarterFourText);
    });
    it("shows sr alert last day of the window (Jan 31)", () => {
      vi.spyOn(authFunctions, "isDRUser").mockReturnValue(false);
      const today = moment("2025-01-31");
      const result = getDueDateAlert(today);
      expect(result.showAlert).toBe(true);
      expect(result.heading).toBe(Quarter4Heading);
      expect(result.text).toBe(SRQuarterFourText);
    });
  });
});
