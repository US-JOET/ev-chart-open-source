/**
 * Component to display the label and tooltip for station form.
 * @packageDocumentation
 **/
import React from "react";

import { Icon, Label, Tooltip } from "evchartstorybook";

import CustomLink from "../../../../components/Tooltip/tooltips";

interface FieldEntryInfo {
  formLabel: string;
  tooltipLabel?: string;
  htmlFor: string;
  requiredField?: boolean;
}

export const FormLabelAndTooltip: React.FC<FieldEntryInfo> = ({
  formLabel,
  tooltipLabel,
  htmlFor,
  requiredField,
}): React.ReactElement => {
  return (
    <div className="label-tooltip-container fixed-width-tooltip">
      <Label htmlFor={htmlFor} className={requiredField ? `${htmlFor} required-field` : htmlFor}>
        {formLabel}
      </Label>
      {tooltipLabel && (
        <Tooltip label={tooltipLabel} asCustom={CustomLink}>
          <Icon.InfoOutline className="tooltip-icon" />
        </Tooltip>
      )}
    </div>
  );
};

export default FormLabelAndTooltip;
