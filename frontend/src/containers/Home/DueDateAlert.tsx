/**
 * Helper file to determine if a due date alert is approaching.
 * @packageDocumentation
 **/
import moment from "moment";
import { isDRUser } from "../../utils/authFunctions";

export const AnnualOneTimeHeading = "Annual & One-Time Data due March 1st";
export const Quarter1Heading = "Quarter 1 (Jan-Mar) Data due April 30th";
export const Quarter2Heading = "Quarter 2 (Apr-Jun) Data due July 31st";
export const Quarter3Heading = "Quarter 3 (Jul-Sep) Data due October 31st";
export const Quarter4Heading = "Quarter 4 (Oct-Dec) Data due January 31st";

export const DRAnnualOneTimeText =
  "For stations operational in the preceding year, you must submit annual and one-time data (modules 5, 6, 7, 8, 9) by March 1st.";
export const SRAnnualOneTimeText =
  "For stations operational in the preceding year, submit annual and one-time data (modules 5-9) for review ahead of the deadline. Direct recipients (i.e. state agencies) need time to review/ approve each submission.";

export const DRQuarterOneText =
  "For stations operational on/before March 31st, you must submit Quarter 1 data (modules 2, 3, 4) by April 30th.";
export const SRQuarterOneText =
  "For stations operational on/before March 31st, submit Quarter 1 data (modules 2-4) for review ahead of the deadline. Direct recipients (i.e. state agencies) need time to review/ approve each submission.";

export const DRQuarterTwoText =
  "For stations operational on/before June 30th, you must submit Quarter 2 data (modules 2, 3, 4) by July 31st.";
export const SRQuarterTwoText =
  "For stations operational on/before June 30th, submit Quarter 2 data (modules 2-4) for review ahead of the deadline. Direct recipients (i.e. state agencies) need time to review/ approve each submission.";

export const DRQuarterThreeText =
  "For stations operational on/before September 30th, you must submit Quarter 3 data (modules 2, 3, 4) by October 31st.";
export const SRQuarterThreeText =
  "For stations operational on/before September 30th, submit Quarter 3 data (modules 2-4) for review ahead of the deadline. Direct recipients (i.e. state agencies) need time to review/ approve each submission.";

export const DRQuarterFourText =
  "For stations operational on/before December 31st, you must submit Quarter 4 data (modules 2, 3, 4) by January 31st.";
export const SRQuarterFourText =
  "For stations operational on/before December 31st, submit Quarter 4 data (modules 2-4) for review ahead of the deadline. Direct recipients (i.e. state agencies) need time to review/ approve each submission.";

/**
 * Function to determine if the current date falls within an alert window for
 * an upcoming submission period
 * Module Type        | Due Date | Alert Starts | Alert Ends
 * Annual & One-Time  | Mar 1    | Feb 1        | Mar 1
 * Quarter 1          | Apr 30   | Mar 31       | Apr 30
 * Quarter 2          | Jul 31   | Jun 30       | Jul 31
 * Quarter 3          | Oct 31   | Sep 30       | Oct 31
 * Quarter 4          | Jan 31   | Jan 1        | Jan 31
 * @param today the current day
 * @returns an object with the relevant alert text, if applicable
 */
export function getDueDateAlert(today: moment.Moment) {
  const annualOneTimeDueDate = moment(`${today.year()}-03-01`);
  const quarterOneDueDate = moment(`${today.year()}-04-30`);
  const quarterTwoDueDate = moment(`${today.year()}-07-31`);
  const quarterThreeDueDate = moment(`${today.year()}-10-31`);
  const quarterFourDueDate = moment(`${today.year()}-01-31`);

  const priorAnnualOneTime = moment(annualOneTimeDueDate).clone().subtract(1, "month");
  const priorQuarterOne = moment(quarterOneDueDate).clone().subtract(1, "month");
  const priorQuarterTwo = moment(quarterTwoDueDate).clone().subtract(1, "month");
  const priorQuarterThree = moment(quarterThreeDueDate).clone().subtract(1, "month");
  const priorQuarterFour = moment(quarterFourDueDate).clone().subtract(1, "month");

  if (today.isBetween(priorAnnualOneTime, annualOneTimeDueDate, "day", "[]")) {
    return {
      showAlert: true,
      heading: AnnualOneTimeHeading,
      text: isDRUser() ? DRAnnualOneTimeText : SRAnnualOneTimeText,
    };
  } else if (today.isBetween(priorQuarterOne, quarterOneDueDate, "day", "[]")) {
    return {
      showAlert: true,
      heading: Quarter1Heading,
      text: isDRUser() ? DRQuarterOneText : SRQuarterOneText,
    };
  } else if (today.isBetween(priorQuarterTwo, quarterTwoDueDate, "day", "[]")) {
    return {
      showAlert: true,
      heading: Quarter2Heading,
      text: isDRUser() ? DRQuarterTwoText : SRQuarterTwoText,
    };
  } else if (today.isBetween(priorQuarterThree, quarterThreeDueDate, "day", "[]")) {
    return {
      showAlert: true,
      heading: Quarter3Heading,
      text: isDRUser() ? DRQuarterThreeText : SRQuarterThreeText,
    };
  }
  if (today.isBetween(priorQuarterFour, quarterFourDueDate, "day", "[]")) {
    return {
      showAlert: true,
      heading: Quarter4Heading,
      text: isDRUser() ? DRQuarterFourText : SRQuarterFourText,
    };
  }
  return {
    showAlert: false,
    heading: "",
    text: "",
  };
}
