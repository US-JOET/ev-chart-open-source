/**
 * Add user form.
 * @packageDocumentation
 **/
import React, { useState } from "react";
import { useNavigate } from "react-router";

import {
  Alert,
  Breadcrumb,
  BreadcrumbBar,
  BreadcrumbLink,
  Button,
  ButtonGroup,
  ErrorMessage,
  Grid,
  GridContainer,
  Icon,
  Label,
  Select,
  TextInput,
  Tooltip,
} from "evchartstorybook";

import { isDRUser } from "../../../../utils/authFunctions";
import { getOrgName, getOrgID, getOrgFriendlyID } from "../../../../utils/getJWTInfo";
import { PATH_USERS } from "../../../../utils/pathConstants";
import { ROUTE_HOME, ROUTE_USERS } from "../../../../utils/routeConstants";
import { validateEmail } from "../../../../validation/email";

import CancelModal from "../../../../components/Modals/CancelModal/CancelModal";
import CustomLink from "../../../../components/Tooltip/tooltips";

import "./AddUser.css";
import RoleDescriptionModal from "../../../../components/Modals/RoleDescriptionModal/RoleDescriptionModal";

/**
 * Initial error state - all are false (inputs assumed to be correct)
 */
const initialErrorState = {
  role: false,
  firstName: false,
  lastName: false,
  email: false,
};

function AddUser() {
  /**
   * Method for changing the location / route
   */
  const navigate = useNavigate();

  /**
   * Get the api and base url from the environment variables
   */
  const BASE_URL = import.meta.env.VITE_PUBLIC_URL;
  const API_URL = import.meta.env.VITE_API_URL;

  const openRoleDescriptionModal = () => {
    setIsRoleDescriptionModalOpen(true);
  };

  const closeRoleDescriptionModal = () => {
    setIsRoleDescriptionModalOpen(false);
  };

  /**
   * Form state values for API submission
   */
  const [addUserValues, setAddUserValues] = useState({
    role: "",
    firstName: "",
    lastName: "",
    email: "",
  });

  const [emailFormatError, setEmailFormatError] = useState<boolean>(false);
  const [formValidity, setFormValidity] = useState<{ [key: string]: boolean }>(initialErrorState);
  const [incorrectValues, setIncorrectValues] = useState<string[]>([]);
  const [duplicateUserError, setDuplicateUserError] = useState<boolean>(false);
  const [isRoleDescriptionModalOpen, setIsRoleDescriptionModalOpen] = useState(false);

  /**
   * Get org info
   */
  const orgName = getOrgName();
  const orgId = getOrgID();
  const orgFriendlyId = getOrgFriendlyID();

  /**
   * Control open / close for cancel modal
   */
  const [isCancelModalOpen, setCancelModalOpen] = useState(false);
  const openModal = () => {
    setCancelModalOpen(true);
  };
  const closeModal = () => {
    setCancelModalOpen(false);
  };

  /**
   * Function to update fields in the form
   * @param fieldName the field being updated
   * @param value the value being set
   */
  const updateField = (fieldName: string, value: any): any => {
    setAddUserValues((prevState) => ({
      ...prevState,
      [fieldName]: value,
    }));

    setFormValidity((prevValidity) => ({
      ...prevValidity,
      [fieldName]: false,
    }));

    if (fieldName === "email") {
      setEmailFormatError(false);
    }
  };

  /**
   * Function to check if a field / input contains an error
   * @param field the field being checked
   * @returns the class name
   */
  function inputValid(field: boolean): string {
    if (field) {
      return "usa-input--error";
    } else {
      return "";
    }
  }

  /**
   * Handle Add user
   */
  const handleAddUser = async () => {
    setIncorrectValues([]);
    setDuplicateUserError(false);

    const updatedFormValidity = { ...formValidity };

    // Role
    if (addUserValues.role === undefined || addUserValues.role === "") {
      updatedFormValidity.role = true;
      setIncorrectValues((prevArray) => [...prevArray, "Role"]);
    }

    // First name
    if (addUserValues.firstName.trim() === "") {
      updatedFormValidity.firstName = true;
      setIncorrectValues((prevArray) => [...prevArray, "First Name"]);
    }

    // Last name
    if (addUserValues.lastName.trim() === "") {
      updatedFormValidity.lastName = true;
      setIncorrectValues((prevArray) => [...prevArray, "Last Name"]);
    }

    // Email
    const emailFormat = validateEmail(addUserValues.email.trim());
    const noEmailValue = addUserValues.email.trim() === "";
    if (noEmailValue || !emailFormat) {
      updatedFormValidity.email = true;
      setIncorrectValues((prevArray) => [...prevArray, "Email"]);
      if (!noEmailValue) {
        setEmailFormatError(true);
      }
    }

    setFormValidity(updatedFormValidity);

    const isFormValid = Object.values(updatedFormValidity).every((valid) => !valid);

    if (isFormValid) {
      const APIPostBody = {
        org_name: orgName,
        org_id: orgId,
        first_name: addUserValues.firstName,
        last_name: addUserValues.lastName,
        email: addUserValues.email,
        role: addUserValues.role,
      };

      const access_token = localStorage.getItem("access_token");

      fetch(`${API_URL}${PATH_USERS}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `${access_token}`,
        },
        body: JSON.stringify(APIPostBody),
      })
        .then((response) => {
          if (response.ok) {
            navigate(ROUTE_USERS, { state: { success: true } });
          } else {
            throw response;
          }
        })
        .catch((err) => {
          const errorCode = err.status;
          if (errorCode === 409) {
            setDuplicateUserError(true);
            window.scrollTo({ top: 0, behavior: "smooth" });
          }
        });
    } else {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  /**
   * List of available roles
   */
  const roleList = {
    admin: "Admin",
    ...(isDRUser() && { viewer: "Viewer" }),
  };

  const userRoleList = Object.entries(roleList).map(([key, value]) => (
    <option value={key} key={key}>
      {value}
    </option>
  ));

  /**
   * Breadcrumb bar for page
   * @returns the breadcrumb bar
   */
  const DefaultBreadcrumb = (): React.ReactElement => (
    <BreadcrumbBar className="add-user-breadcrumbs">
      <Breadcrumb>
        <BreadcrumbLink href={ROUTE_HOME}>
          <span>Home</span>
        </BreadcrumbLink>
      </Breadcrumb>
      <Breadcrumb>
        <BreadcrumbLink href={`${BASE_URL}${ROUTE_USERS}`}>
          <span>Users</span>
        </BreadcrumbLink>
      </Breadcrumb>
      <Breadcrumb current>
        <span>Add User</span>
      </Breadcrumb>
    </BreadcrumbBar>
  );

  return (
    <div className="add-user">
      <div>
        <GridContainer>
          <DefaultBreadcrumb />
        </GridContainer>
      </div>
      <div className="usa-section" style={{ paddingTop: 0 }}>
        <GridContainer>
          {duplicateUserError && (
            <Alert type="error" headingLevel="h3" heading="Please correct the following fields:">
              This user already exists
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
          <Grid row>
            <Grid col={8}>
              <h1 className="add-user-heading">Add User</h1>
            </Grid>
          </Grid>
          <div className="org-details-container">
            <Grid row>
              <Grid col={8}>
                <h3 className="add-user-subheading">Organization Details</h3>
              </Grid>
            </Grid>
            <div className="org-details-field">
              <Grid row>
                <Grid col={8}>
                  <h4 className="organization-label">Organization Name</h4>
                </Grid>
              </Grid>
              <Grid row>
                <Grid col={8}>
                  <p>{orgName}</p>
                </Grid>
              </Grid>
            </div>
            <div className="org-details-field">
              <Grid row>
                <Grid col={8}>
                  <h4 className="organization-label">Organization ID</h4>
                </Grid>
              </Grid>
              <Grid row>
                <Grid col={8}>
                  <p>{orgFriendlyId}</p>
                </Grid>
              </Grid>
            </div>
          </div>
          <div className="user-details-container">
            <Grid row>
              <Grid col={8}>
                <h3 className="user-details-heading">User Details</h3>
              </Grid>
            </Grid>
            <Grid row>
              <Grid col={8}>
                {isDRUser() ? (
                  <p className="admin-info">
                    Are you unsure which role to assign this user?{" "}
                    <a href="javascript:void(0)" onClick={openRoleDescriptionModal}>
                      Review available roles and permissions available in EV-ChART.
                    </a>
                  </p>
                ) : (
                  <p className="admin-info">
                    The administrator role can submit data and manage other accounts for this organization.
                  </p>
                )}

              </Grid>
            </Grid>
            <Grid row className="add-user-field">
              <Grid col={8}>
                <Label htmlFor="input-state" className="required-field">
                  Role
                </Label>
                <Select
                  className={inputValid(formValidity.role)}
                  id="role"
                  name="role"
                  onChange={(e: any) => updateField("role", e.target.value)}
                >
                  <option value=""> - Select - </option>
                  {userRoleList}
                </Select>
                {formValidity.role && <ErrorMessage>This field is required</ErrorMessage>}
              </Grid>
            </Grid>
            <Grid row className="add-user-field">
              <Grid col={8}>
                <Label htmlFor="firstName" className="required-field">
                  First Name
                </Label>
                <TextInput
                  id="firstName"
                  name="firstName"
                  type="text"
                  className={inputValid(formValidity.firstName)}
                  onChange={(e) => updateField("firstName", e.target.value)}
                />
                {formValidity.firstName && <ErrorMessage>This field is required</ErrorMessage>}
              </Grid>
            </Grid>
            <Grid row className="add-user-field">
              <Grid col={8}>
                <Label htmlFor="lastName" className="required-field">
                  Last Name
                </Label>
                <TextInput
                  id="lastName"
                  name="lastName"
                  type="text"
                  className={inputValid(formValidity.lastName)}
                  onChange={(e) => updateField("lastName", e.target.value)}
                />
                {formValidity.lastName && <ErrorMessage>This field is required</ErrorMessage>}
              </Grid>
            </Grid>
            <Grid row className="add-user-field">
              <Grid col={8}>
                <div className="label-tooltip-container">
                  <Label htmlFor="email" className="required-field">
                    Email
                  </Label>
                  <Tooltip
                    label={"This email address will be used by the new user to log into EV-ChART."}
                    asCustom={CustomLink}
                  >
                    <Icon.InfoOutline className="tooltip-icon" />
                  </Tooltip>
                </div>
                <TextInput
                  id="email"
                  name="email"
                  type="text"
                  className={inputValid(formValidity.email)}
                  onChange={(e) => updateField("email", e.target.value)}
                />
                {formValidity.email && !emailFormatError && <ErrorMessage>This field is required</ErrorMessage>}
                {emailFormatError && <ErrorMessage>Invalid email address format</ErrorMessage>}{" "}
              </Grid>
            </Grid>
          </div>
          <div className="add-user-buttons-container">
            <Grid row className="add-user-field">
              <Grid col={8}>
                <ButtonGroup>
                  <Button type="button" onClick={handleAddUser}>
                    Add
                  </Button>
                  <Button onClick={openModal} type="button" unstyled className="padding-105 text-center">
                    Cancel
                  </Button>
                </ButtonGroup>
              </Grid>
            </Grid>
          </div>
        </GridContainer>
        {isCancelModalOpen && <CancelModal navigateUrl={ROUTE_USERS} onClose={closeModal} />}
        {isRoleDescriptionModalOpen && <RoleDescriptionModal onClose={closeRoleDescriptionModal} />}
      </div>
    </div>
  );
}

export default AddUser;
