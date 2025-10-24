/**
 * Users landing page.
 * @packageDocumentation
 **/
import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router";

import { Alert, Breadcrumb, BreadcrumbBar, BreadcrumbLink, Button, GridContainer, Grid } from "evchartstorybook";

import { isAdmin } from "../../../../utils/authFunctions";
import { FeatureFlagEnum, getFeatureFlagValue, getFeatureFlagList } from "../../../../utils/FeatureToggle";
import { ROUTE_ADD_USER, ROUTE_HOME } from "../../../../utils/routeConstants";

import RemoveUserModal from "../../../../components/Modals/RemoveUserModal/RemoveUserModal";
import ReInviteUserModal from "../../../../components/Modals/ReInviteUserModal/ReInviteUserModal";
import UserOverview from "../../../../components/UserOverview/UserOverview";
import UserSummary from "../../../../components/UserSummary/UserSummary";

import "./Users.css";

function Users() {
  /**
   * Method for changing the location / route
   */
  const navigate = useNavigate();
  const { state } = useLocation();

  /**
   * Get the api url from the environment variables
   */
  const BASE_URL = import.meta.env.VITE_PUBLIC_URL;

  /**
   * Feature flag management
   */
  const [addUserFeatureFlag, setAddUserFeatureFlag] = useState(false);
  useEffect(() => {
    getFeatureFlagList().then((results) => {
      setAddUserFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.AddUser));
    });
  }, []);

  /**
   * State variables to pass user info to the remove modal
   */
  const [currEmail, setCurrEmail] = useState("");
  const [currName, setCurrName] = useState("");
  const [currRole, setCurrRole] = useState("");

  /**
   * State variables for the various banners
   */
  const [successBanner, setSuccessBanner] = useState(false);
  const [removeSuccessBanner, setRemoveSuccessBanner] = useState(false);
  const [reInviteSuccessBanner, setReInviteSuccessBanner] = useState(false);
  const [patchUserFailedBanner, setPatchUserFailedBanner] = useState(false);

  /**
   * State variables for modals
   */
  const [isRemoveUserModalOpen, setRemoveUserModalOpen] = useState(false);
  const [isReInviteUserModalOpen, setReInviteUserModalOpen] = useState(false);

  /**
   * Function to open / close remove user modal
   */
  const openRemoveUserModal = () => {
    setRemoveUserModalOpen(true);
  };
  const closeRemoveUserModal = () => {
    setRemoveUserModalOpen(false);
  };

  /**
   * Function to open / close reinvite modal
   */
  const openReInviteUserModal = () => {
    setReInviteUserModalOpen(true);
  };
  const closeReInviteUserModal = () => {
    setReInviteUserModalOpen(false);
  };

  /**
   * Functions to set the info on current user selection
   * @param id the id being set
   */
  const getCurrentEmail = (id: string) => {
    setCurrEmail(id);
  };
  const getCurrentName = (id: string) => {
    setCurrName(id);
  };
  const getCurrentRole = (id: string) => {
    setCurrRole(id);
  };

  /**
   * Breadcrumb bar for page
   * @returns the breadcrumb bar
   */
  const DefaultBreadcrumb = (): React.ReactElement => (
    <BreadcrumbBar>
      <Breadcrumb>
        <BreadcrumbLink href={`${BASE_URL}${ROUTE_HOME}`}>
          <span>Home</span>
        </BreadcrumbLink>
      </Breadcrumb>
      <Breadcrumb current>
        <span>Users</span>
      </Breadcrumb>
    </BreadcrumbBar>
  );

  /**
   * Update success banner accordingly if existing state
   */
  useEffect(() => {
    if (state) {
      setSuccessBanner(true);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
    if (localStorage.getItem("userRemoved") === "true") {
      setRemoveSuccessBanner(true);
      localStorage.setItem("userRemoved", "false");
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
    if (localStorage.getItem("userInviteResent") === "true") {
      setReInviteSuccessBanner(true);
      localStorage.setItem("userInviteResent", "false");
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
    if (localStorage.getItem("patchUserFailed") === "true") {
      setPatchUserFailedBanner(true);
      localStorage.setItem("patchUserFailed", "false");
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }, []);

  return (
    <div className="Stations">
      <div>
        <GridContainer>
          <DefaultBreadcrumb />
        </GridContainer>
      </div>
      <div id="one-time-submission">
        <div className="usa-section" style={{ paddingTop: 0 }}>
          <GridContainer>
            <Grid row>
              <Grid col={10}>
                <h1 className="users-heading"> Users </h1>
              </Grid>
              <Grid className="add-user-button-container" col={2}>
                {isAdmin() && addUserFeatureFlag && (
                  <Button type="button" className="add-user-button" onClick={() => navigate(ROUTE_ADD_USER)}>
                    Add User
                  </Button>
                )}
              </Grid>
            </Grid>
            <Grid row>
              <Grid col={12}>
                {successBanner && (
                  <Alert
                    type="success"
                    headingLevel="h3"
                    className="user-success-banner"
                    heading="User added successfully"
                  >
                    The user added will receive an email notification with instructions on how to activate their
                    account.
                  </Alert>
                )}
                {removeSuccessBanner && (
                  <Alert
                    type="success"
                    headingLevel="h3"
                    className="user-success-banner"
                    heading="User removed successfully"
                  >
                    This user is no longer able to upload or handle data on your organization's behalf. This user will
                    not be notified of their account deactivation.
                  </Alert>
                )}
                {reInviteSuccessBanner && (
                  <Alert
                    type="success"
                    headingLevel="h3"
                    className="user-success-banner"
                    heading="User invitation resent successfully"
                  >
                    The added user will receive an email notification with instructions for activating their account.
                    The user has 30 days to log in to EV-ChART before their invitation will expire.
                  </Alert>
                )}
                {patchUserFailedBanner && (
                  <Alert type="error" headingLevel="h3" className="user-error-banner" heading="An Error Occured!">
                    An error occured when attemping an action on {currEmail}. Please try again later, if the problem
                    persists please reach out to EV-ChART help.
                  </Alert>
                )}
              </Grid>
            </Grid>
            <UserOverview />
            <Grid row>
              <Grid className="users-subheading-container" col={12}>
                <h2 className="users-subheading"> Users </h2>
              </Grid>
            </Grid>
            <UserSummary
              sortByStatus={state ? true : false}
              setRemoveUserModal={openRemoveUserModal}
              setReInviteUserModal={openReInviteUserModal}
              setCurrEmail={getCurrentEmail}
              setCurrName={getCurrentName}
              setCurrRole={getCurrentRole}
            />
            {isRemoveUserModalOpen && <RemoveUserModal email={currEmail} onClose={closeRemoveUserModal} />}
            {isReInviteUserModalOpen && (
              <ReInviteUserModal email={currEmail} name={currName} role={currRole} onClose={closeReInviteUserModal} />
            )}
          </GridContainer>
        </div>
      </div>
    </div>
  );
}

export default Users;
