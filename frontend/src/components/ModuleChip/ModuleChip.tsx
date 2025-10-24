/**
 * styled module chips used throughout the application
 * @packageDocumentation
 **/
import React from "react";

import { Chip, Tooltip } from "evchartstorybook";

import CustomLink from "../Tooltip/tooltips";

interface ModuleChipProps {
  submission_status: string;
}

/**
 * ModuleChip
 * @param submission_status the submission status
 * @returns the styled chip
 */
export const ModuleChip: React.FC<ModuleChipProps> = ({ submission_status }): React.ReactElement => {
  let moduleChip: React.ReactElement;
  switch (submission_status.toUpperCase()) {
    case "DRAFT":
    default:
      moduleChip = <Chip type="info">Draft</Chip>;
      break;
    case "PENDING":
    case "PENDING APPROVAL":
      moduleChip = <Chip type="warning">Pending</Chip>;
      break;
    case "SUBMITTED":
      moduleChip = <Chip type="success">Submitted</Chip>;
      break;
    case "APPROVED":
      moduleChip = <Chip type="success">Approved</Chip>;
      break;
    case "REJECTED":
      moduleChip = <Chip type="error">Rejected</Chip>;
      break;
    case "ERROR":
      moduleChip = <Chip type="error">Error</Chip>;
      break;
    case "PROCESSING":
      moduleChip = (
        <Tooltip
          label={"This draft is uploading to the system and will be available to review soon."}
          asCustom={CustomLink}
        >
          <Chip type="processing">
            Uploading
            <br />
            Draft
          </Chip>
        </Tooltip>
      );
      break;
  }
  return moduleChip;
};

export default ModuleChip;
