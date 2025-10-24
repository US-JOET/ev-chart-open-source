/**
 * Form for jo / dr to add organizations.
 * @packageDocumentation
 **/
import React, { createRef, useState, useEffect } from "react";

import {
  Alert,
  Breadcrumb,
  BreadcrumbBar,
  BreadcrumbLink,
  Button,
  ComboBox,
  ComboBoxRef,
  ErrorMessage,
  Fieldset,
  Grid,
  GridContainer,
  Icon,
  Label,
  Radio,
  Spinner,
  TextInput,
  Tooltip,
} from "evchartstorybook";

import { OrganizationSummary } from "../../../interfaces/Organization/organizations-interface";
import { OptionsList } from "../../../interfaces/ui-components-interfaces";

import { isDRUser, isJOUser } from "../../../utils/authFunctions";
import { PATH_DIRECT_RECIPIENTS, PATH_SUB_RECIPIENTS } from "../../../utils/pathConstants";
import { ROUTE_HOME, ROUTE_STATIONS } from "../../../utils/routeConstants";

import { validateEmail } from "../../../validation/email";

import ConfirmOrganizationModal from "../../../components/Modals/ConfirmOrganizationModal/ConfirmOrganizationModal";
import CustomLink from "../../../components/Tooltip/tooltips";

import "./AddOrg.css";

/**
 * Form values for a new organization (all empty)
 */
const newOrgEmptyValues = {
  orgName: "",
  firstName: "",
  lastName: "",
  email: "",
};

/**
 * Template for organization summary for combobox options
 */
const OrgInfo = {
  org_id: "",
  name: "",
  org_friendly_id: "",
};

/**
 * Initial error state - all are false (inputs assumed to be correct)
 */
const initialErrorState = {
  orgName: false,
  orgType: false,
  firstName: false,
  lastName: false,
  email: false,
};

/**
 * AddOrg
 * @returns form for jo / dr to add organizations
 */
function AddOrg() {
  /**
   * Get the api url and environment variables
   */
  const API_URL = import.meta.env.VITE_API_URL;

  /**
   * Get id token for endpoint authorization
   */
  const id_token = localStorage.getItem("id_token");

  /**
   * Form state values for API submission
   */
  const [addOrgValues, setaddOrgValues] = useState(newOrgEmptyValues);

  /**
   * Ref for combobox
   */
  const refOrganizationName = createRef<ComboBoxRef>();

  /**
   * State variable for tracking if options have returned from endpoint, render spinner otherwise
   */
  const [renderSelectionOptions, setRenderSelectionOptions] = useState<boolean>(false);

  /**
   * State variable for tracking form validity
   */
  const [formValidity, setFormValidity] = useState<{ [key: string]: boolean }>(initialErrorState);

  /**
   * State variable for rendering the error banner with all invalid fields
   */
  const [incorrectValues, setIncorrectValues] = useState<string[]>([]);

  /**
   * State variable for capturing invalid email error
   */
  const [emailFormatError, setEmailFormatError] = useState<boolean>(false);

  /**
   * State variable for rendering the error banner for invalid user error
   */
  const [invalidUserError, setInvalidUserError] = useState<boolean>(false);

  /**
   * State variable for rendering the error banner for duplicate org
   */
  const [duplicateOrg, setDuplicateOrg] = useState<boolean | null>(null);

  /**
   * State variable for rendering the success banner upon org creation
   */
  const [successBanner, setSuccessBanner] = useState<boolean>(false);

  /**
   * The type of organization being created (if JO user)
   */
  const [orgTypeSelection, setOrgTypeSelection] = useState<string | null>(null);

  /**
   * The options returned from the /org/direct-recipients endpoint
   */
  const [directRecipients, setDirectRecipients] = useState<OrganizationSummary[] | null>(null);

  /**
   * The options returned from the /org/subrecipients endpoint
   */
  const [subRecipients, setSubrecipients] = useState<OrganizationSummary[] | null>(null);

  /**
   * The options to be rendered in the combobox for checking against duplicate organizations
   */
  const [existingOrganizationsOptions, setExistingOrganizationOptions] = useState<OrganizationSummary[]>([OrgInfo]);

  /**
   * State variables / functions to manage if confirm organization modal is open
   */
  const [isConfirmOrganizationModalOpen, setIsConfirmOrganizationModalOpen] = useState(false);
  const openConfirmOrganizationModal = () => {
    setIsConfirmOrganizationModalOpen(true);
  };
  const closeConfirmOrganizationModal = () => {
    setIsConfirmOrganizationModalOpen(false);
  };

  /**
   * Event tied to updating a field
   * @param fieldName the field to be updated
   * @param value the value to be set to
   */
  const updateField = (fieldName: string, value: any): any => {
    setaddOrgValues((prevState) => ({
      ...prevState,
      [fieldName]: value,
    }));

    setFormValidity((prevValidity) => ({
      ...prevValidity,
      [fieldName]: false,
    }));

    if (fieldName === "email") {
      setEmailFormatError(false);
      setInvalidUserError(false);
    }
  };

  /**
   * Function to set class name based on if field data is valid/ invalid
   * @param field boolean if the field contains an error
   * @param type the type of field in the ui form
   * @returns the appropriate class name
   */
  function inputValid(field: boolean, type: string): string {
    if (field && type === "combobox") {
      return "error-combobox";
    } else if (field) {
      return "usa-input--error";
    } else {
      return "";
    }
  }

  /**
   * Handle Add Organization / form submission
   */
  const handleAddOrg = async () => {
    setIncorrectValues([]);
    setEmailFormatError(false);

    const updatedFormValidity = { ...formValidity };

    // Org Type
    if (isJOUser() && orgTypeSelection === null) {
      updatedFormValidity.orgType = true;
      setIncorrectValues((prevArray) => [...prevArray, "Organization Type"]);
    }

    // Role
    if (addOrgValues.orgName === undefined || addOrgValues.orgName === "") {
      updatedFormValidity.orgName = true;
      setIncorrectValues((prevArray) => [...prevArray, "Organization Name"]);
    }

    // First name
    if (addOrgValues.firstName.trim() === "") {
      updatedFormValidity.firstName = true;
      setIncorrectValues((prevArray) => [...prevArray, "New Administrator First Name"]);
    }

    // Last name
    if (addOrgValues.lastName.trim() === "") {
      updatedFormValidity.lastName = true;
      setIncorrectValues((prevArray) => [...prevArray, "New Administrator Last Name"]);
    }

    // Email
    const emailFormat = validateEmail(addOrgValues.email.trim());
    const noEmailValue = addOrgValues.email.trim() === "";
    if (noEmailValue || !emailFormat) {
      updatedFormValidity.email = true;
      setIncorrectValues((prevArray) => [...prevArray, "New Administrator Email"]);
      if (!noEmailValue) {
        setEmailFormatError(true);
      }
    }

    setFormValidity(updatedFormValidity);

    const isFormValid = Object.values(updatedFormValidity).every((valid) => !valid);
    if (isFormValid) {
      openConfirmOrganizationModal();
    } else {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  /**
   * Get list of all SR organizations
   */
  useEffect(() => {
    fetch(`${API_URL}${PATH_SUB_RECIPIENTS}`, {
      method: "GET",
      headers: {
        Authorization: `${id_token}`,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        setSubrecipients(data);
      })
      .catch((err) => {
        console.log(err.message);
      });
  }, []);

  /**
   * If JO, also get all DR organizations
   */
  useEffect(() => {
    if (isJOUser()) {
      fetch(`${API_URL}${PATH_DIRECT_RECIPIENTS}`, {
        method: "GET",
        headers: {
          Authorization: `${id_token}`,
        },
      })
        .then((response) => response.json())
        .then((data) => {
          setDirectRecipients(data);
        })
        .catch((err) => {
          console.log(err.message);
        });
    }
  }, []);

  /**
   * Determine what organizations to render in the combobox
   * If JO, all orgs should be present. If DR, only subrecipients should be shown
   */
  useEffect(() => {
    if (isDRUser() && subRecipients !== null) {
      setExistingOrganizationOptions(subRecipients);
      setRenderSelectionOptions(true);
    } else if (directRecipients !== null && subRecipients !== null) {
      const combinedList = Array.from(
        new Map([...subRecipients, ...directRecipients].map((org) => [org.org_id, org])).values(),
      );
      setExistingOrganizationOptions(combinedList);
      setRenderSelectionOptions(true);
    }
  }, [directRecipients, subRecipients]);

  /**
   * The existing organizations options converted to a list for use within the combobox component
   */
  const existingOrganizationsList: OptionsList[] = existingOrganizationsOptions?.map(
    (item: { org_id: string; name: string; org_friendly_id: string }) => ({
      value: item.org_id,
      label: item.name,
    }),
  );
  const options = [...existingOrganizationsList];

  /**
   * Event tied to input change in the combobox
   * As user types, filters against the found options and appends their current text as a
   * new option if not found
   * @param e the value they are typing into the combobox
   */
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { value } = e.target;

    if (value && existingOrganizationsList.findIndex((f) => f.value === value) < 0) {
      if (options.length === existingOrganizationsList.length) {
        // Add new option to end of list
        options.push({ value, label: value });
      } else {
        // Rewrite the new option
        options[options.length - 1] = { value, label: `Add new: ${value}` };
      }
    }
  };

  /**
   * For JO only, event tied to checkbox for organization type
   * @param value the type of organization being created
   */
  const updateOrgTypeField = (value: string): any => {
    setSuccessBanner(false);
    setOrgTypeSelection(value);
    setFormValidity((prevValidity) => ({ ...prevValidity, orgType: false }));
  };

  /**
   * Error state for if a duplicate user is added
   */
  const setDuplicateUser = () => {
    setFormValidity((prevValidity) => ({ ...prevValidity, email: true }));
    setIncorrectValues((prevArray) => [...prevArray, "New Administrator Email"]);
    setInvalidUserError(true);
    setIsConfirmOrganizationModalOpen(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  /**
   * Set success banner when org is adding and clear all selections
   */
  const setOrgSuccess = () => {
    refOrganizationName.current?.clearSelection();
    setaddOrgValues(newOrgEmptyValues);
    setSuccessBanner(true);
    setIsConfirmOrganizationModalOpen(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  /**
   * Event tied to updating the name of the new organization in the form
   * If the name entered matches an existing organization, set error state
   * @param value the value the user is typing in the field
   */
  const handleOrganizationNameChange = (value: any) => {
    updateField("orgName", value);
    if (value === undefined) {
      setDuplicateOrg(null);
    } else if (existingOrganizationsOptions.find((org) => org.org_id === value)) {
      // made a selection from the combobox
      setFormValidity((prevValidity) => ({ ...prevValidity, orgName: true }));
      setDuplicateOrg(true);
    } else if (existingOrganizationsOptions.find((org) => org.name.toUpperCase() === value.trim().toUpperCase())) {
      //type in a new org with same name
      setFormValidity((prevValidity) => ({ ...prevValidity, orgName: true }));
      setDuplicateOrg(true);
    } else {
      setDuplicateOrg(false);
    }
  };

  /**
   * Get the success header for adding an org
   * @returns the appropriate text based on what organization was created
   */
  const getSuccessBannerHeader = () => {
    if (isDRUser()) {
      return "Subrecipient/contractor organization added successfully";
    }
    return `${orgTypeSelection === "direct-recipient" ? "Direct Recipient" : "Subrecipient/contractor"} organization added successfully`;
  };

  /**
   * Get the success text for adding an org
   * @returns the appropriate text based on the user that created the organization
   */
  const getSuccessBannerText = () => {
    if (isDRUser()) {
      return "You may now authorize this organization to submit data on your behalf. The administrator added will receive an email notification with instructions on how to activate their account.";
    }
    return "The administrator added will receive an email notification with instructions on how to activate their account.";
  };

  /**
   * Breadcrumb bar for page
   * @returns the breadcrumb bar
   */
  const DefaultBreadcrumb = (): React.ReactElement => (
    <BreadcrumbBar className="add-org-breadcrumbs">
      <Breadcrumb>
        <BreadcrumbLink href={ROUTE_HOME}>
          <span>Home</span>
        </BreadcrumbLink>
      </Breadcrumb>
      <Breadcrumb current>
        <span>{isJOUser() ? "Add Organization" : "Add Subrecipient/Contractor Organization"}</span>
      </Breadcrumb>
    </BreadcrumbBar>
  );

  return (
    <div className="add-org">
      <div>
        <GridContainer>
          <DefaultBreadcrumb />
        </GridContainer>
      </div>
      <div className="usa-section" style={{ paddingTop: 0 }}>
        <GridContainer>
          <Grid row>
            <Grid col={12}>
              {successBanner && (
                <Alert type="success" headingLevel="h3" heading={getSuccessBannerHeader()}>
                  {getSuccessBannerText()}
                </Alert>
              )}

              {incorrectValues.length > 0 && (
                <Alert type="error" headingLevel="h3" heading="Please correct the following fields:">
                  <ul>
                    {incorrectValues.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </Alert>
              )}
            </Grid>
          </Grid>
        </GridContainer>

        <GridContainer>
          <Grid row>
            <Grid col={8}>
              <h1>{isJOUser() ? "Add Organization" : "Add Subrecipient/Contractor Organization"}</h1>
            </Grid>
          </Grid>
        </GridContainer>

        <GridContainer>
          <Grid className="add-sr-background-card">
            <Grid row>
              <Grid col={12}>
                <h3 className="new-org-subheading">
                  {isJOUser()
                    ? "Check for Existing Organization"
                    : "Check for Existing Subrecipient/ Contractor Organization"}
                </h3>
              </Grid>
            </Grid>

            {isJOUser() && (
              <div className="jo-select-org-container">
                <Grid row>
                  <Grid col={12}>
                    <Label htmlFor="org-type" className="required-field">
                      Select Organization Type
                    </Label>
                  </Grid>
                </Grid>
                <Grid row gap className="org-type-selection">
                  <Fieldset legendStyle="srOnly">
                    <Radio
                      id="input-dr-radio"
                      name="input-org-radio"
                      className="org-radio-field"
                      label="Direct Recipient Organization"
                      value="direct-recipient"
                      onChange={(e) => updateOrgTypeField(e.target.value)}
                    />
                    <Radio
                      id="input-sr-radio"
                      name="input-org-radio"
                      className="org-radio-field"
                      label="Subrecipient/ Contractor Organization"
                      value="sub-recipient"
                      onChange={(e) => updateOrgTypeField(e.target.value)}
                    />
                  </Fieldset>
                </Grid>
                {formValidity.orgType && <ErrorMessage>This field is required</ErrorMessage>}
              </div>
            )}

            <Grid row>
              <Grid col={12}>
                <p className="admin-info">
                  If {isJOUser() ? "organization " : "subrecipient/contractor "}
                  does not already exist in the dropdown menu, type the new organization name.
                </p>
              </Grid>
            </Grid>

            {renderSelectionOptions ? (
              <Grid row gap>
                <Grid col={8}>
                  <div className="label-tooltip-container">
                    <Label htmlFor="email" className="required-field">
                      Organization Name
                    </Label>
                    <Tooltip
                      label={`The ${isDRUser() ? "subrecipient/contractor" : ""} organization name is used across EV-ChART to track this organization's submission activity. Each organization also has an auto-generated unique ID number that will appear beside its name.`}
                      asCustom={CustomLink}
                    >
                      <Icon.InfoOutline className="tooltip-icon" />
                    </Tooltip>
                  </div>
                  <ComboBox
                    ref={refOrganizationName}
                    id={`input-subrecipient`}
                    name={`input-subrecipient`}
                    options={options}
                    className={inputValid(formValidity.orgName, "combobox")}
                    onChange={(e) => handleOrganizationNameChange(e)}
                    inputProps={{ onChange: handleInputChange }}
                  />
                  {formValidity.orgName && !duplicateOrg && <ErrorMessage>This field is required</ErrorMessage>}
                  {duplicateOrg && <ErrorMessage>This organization exists in EV-ChART</ErrorMessage>}
                </Grid>
              </Grid>
            ) : (
              <div className="dr-selection-spinner-container">
                <Grid row>
                  <Grid className="dr-selection-spinner" col={5}>
                    <Spinner />
                  </Grid>
                </Grid>
              </div>
            )}
            {duplicateOrg === true && (
              <div className="organization-registration-status">
                <h4> This organization is already registered within EV-ChART</h4>
                <p>
                  {" "}
                  To authorize this organization to submit data on your behalf,{" "}
                  <a className="evchart-link" href={ROUTE_STATIONS}>
                    add or edit stations.
                  </a>
                </p>
              </div>
            )}

            {duplicateOrg === false && (
              <div className="organization-registration-status">
                <h4> This organization is new to EV-ChART</h4>
                <p> Ensure the organization name is correct. Then, proceed by adding adminstrator details below.</p>
              </div>
            )}

            <Grid row>
              <Grid col={12}>
                <h3 className="new-org-subheading add-admin-heading">
                  {isJOUser() ? "Add New Organization Administrator " : "Add New Subrecipient/Contractor Administrator"}
                </h3>
              </Grid>
            </Grid>
            <Grid row>
              <Grid col={12}>
                <p className="admin-info">
                  The administrator role can submit data and manage other users for this organization.
                </p>
              </Grid>
            </Grid>

            <Grid row className="add-user-field">
              <Grid col={8}>
                <Label htmlFor="firstName" className="required-field">
                  New Administrator First Name
                </Label>
                <TextInput
                  id="firstName"
                  name="firstName"
                  type="text"
                  className={inputValid(formValidity.firstName, "field")}
                  value={addOrgValues.firstName}
                  disabled={duplicateOrg === true}
                  onChange={(e) => updateField("firstName", e.target.value)}
                />
                {formValidity.firstName && <ErrorMessage>This field is required</ErrorMessage>}
              </Grid>
            </Grid>

            <Grid row className="add-user-field">
              <Grid col={8}>
                <Label htmlFor="lastName" className="required-field">
                  New Administrator Last Name
                </Label>
                <TextInput
                  id="lastName"
                  name="lastName"
                  type="text"
                  className={inputValid(formValidity.lastName, "field")}
                  value={addOrgValues.lastName}
                  disabled={duplicateOrg === true}
                  onChange={(e) => updateField("lastName", e.target.value)}
                />
                {formValidity.lastName && <ErrorMessage>This field is required</ErrorMessage>}
              </Grid>
            </Grid>

            <Grid row className="add-user-field">
              <Grid col={8}>
                <div className="label-tooltip-container">
                  <Label htmlFor="email" className="required-field">
                    New Administrator Email
                  </Label>
                  <Tooltip
                    label={"This email address will be used by the new user to log into EV-ChART."}
                    asCustom={CustomLink}
                  >
                    <Icon.InfoOutline className="tooltip-icon" />
                  </Tooltip>
                </div>
                <div className=" ev-ch-art-form-controls-text-i usa-hint">
                  Use an individual email account and avoid using a general contact email address.
                </div>
                <TextInput
                  id="email"
                  name="email"
                  type="email"
                  className={inputValid(formValidity.email, "field")}
                  value={addOrgValues.email}
                  disabled={duplicateOrg === true}
                  onChange={(e) => updateField("email", e.target.value)}
                />
                {formValidity.email && !emailFormatError && !invalidUserError && (
                  <ErrorMessage>This field is required</ErrorMessage>
                )}
                {emailFormatError && <ErrorMessage>Invalid email address format</ErrorMessage>}
                {invalidUserError && (
                  <ErrorMessage>
                    This email address already exists in EV-ChART. Please contact your subrecipient/contractor for
                    assistance.
                  </ErrorMessage>
                )}
              </Grid>
            </Grid>

            <Grid row>
              <Grid col={8}>
                <Button type="button" onClick={handleAddOrg} disabled={duplicateOrg === true}>
                  Add
                </Button>
              </Grid>
            </Grid>
          </Grid>
        </GridContainer>
        {isConfirmOrganizationModalOpen && (
          <ConfirmOrganizationModal
            onClose={closeConfirmOrganizationModal}
            invalidUser={setDuplicateUser}
            success={setOrgSuccess}
            orgName={addOrgValues.orgName}
            firstName={addOrgValues.firstName}
            lastName={addOrgValues.lastName}
            email={addOrgValues.email}
            orgType={orgTypeSelection}
          />
        )}
      </div>
    </div>
  );
}

export default AddOrg;
