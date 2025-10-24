/**
 * Landing page for stations.
 * @packageDocumentation
 **/
import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router";

import { Button, Breadcrumb, BreadcrumbBar, BreadcrumbLink, GridContainer, Grid, Alert } from "evchartstorybook";

import { StationInfo } from "../../../../interfaces/Stations/stations-interface";

import { isAdmin, isDRUser, isSRUser } from "../../../../utils/authFunctions";
import { FeatureFlagEnum, getFeatureFlagValue, getFeatureFlagList } from "../../../../utils/FeatureToggle";
import { getScope } from "../../../../utils/getJWTInfo";
import { ROUTE_ADD_SR_ORG, ROUTE_HOME, ROUTE_STATION_REGISTRATION } from "../../../../utils/routeConstants";

import StationSummary from "../../../../components/StationSummary/StationSummary";
import ColumnDefinitionsModal from "../../../../components/Modals/ColumnDefinitionModal/ColumnDefinitions";
import RemoveStationModal from "../../../../components/Modals/RemoveStationModal/RemoveStation";

import "./Stations.css";

function Stations() {
  /**
   * Method for changing the location / route
   */
  const navigate = useNavigate();

  /**
   * User / org information
   */
  const recipientType = getScope();

  /**
   * State passed through the application
   */
  const { state } = useLocation();

  /**
   * State variables for controlling the various banners
   */
  const [createSuccessBanner, setCreateSuccessBanner] = useState(false);
  const [rejectSuccessBanner, setRejectSuccessBanner] = useState(false);
  const [removeSuccessBanner, setRemoveSuccessBanner] = useState(false);
  const [updateSuccessBanner, setUpdateSuccessBanner] = useState(false);
  const [successBannerLanugageOnStationCreation, setSuccessBannerLanugageOnStationCreation] = useState("");
  const [rejectBannerLanugage, setRejectBannerLanugage] = useState("");

  /**
   * State variables for managing modals
   */
  const [isColumnDefinitionsModalOpen, setIsColumnDefinitionsModalOpen] = useState(false);
  const [isRemoveStationModalOpen, setIsRemoveStationModalOpen] = useState(false);

  /**
   * Open / close column definitions functions
   */
  const openColumnDefinitionsModal = () => {
    setIsColumnDefinitionsModalOpen(true);
  };
  const closeColumnDefinitionsModal = () => {
    setIsColumnDefinitionsModalOpen(false);
  };

  /**
   * Open / close remove station modal
   */
  const openRemoveStationModal = () => {
    setIsRemoveStationModalOpen(true);
  };
  const closeRemoveStationModal = () => {
    setIsRemoveStationModalOpen(false);
  };

  /**
   * Feature flag management
   */
  const [addSROrgFeatureFlag, setAddSROrgFeatureFlag] = useState(false);
  const [SRAddsStationFeatureFlag, setSRAddsStationFeatureFlag] = useState(false);
  useEffect(() => {
    getFeatureFlagList().then((results) => {
      setAddSROrgFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.AddSROrg));
      setSRAddsStationFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.SRAddsStation));
    });
  }, []);

  /**
   * State variable for the table name
   */
  const [tableName, setTableName] = useState("");

  /**
   * State variable to track station being removed
   */
  const [removedStation, setRemovedStation] = useState<StationInfo>({
    station_uuid: "",
    nickname: "",
    station_id: "",
    removeable: true,
    authorized_subrecipients: "",
    dr_name: "",
    status: "",
    federally_funded: ""
  });

  /**
   * Function to remove a station/ open the remove modal
   * @param station the info for station selected for removal
   */
  const setStationToBeRemoved = (station: StationInfo) => {
    setRemovedStation(station);
  };

  /**
   * Set the removed station modal
   */
  const setBannerRemoveStation = () => {
    setRemoveSuccessBanner(true);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  /**
   * Update success banner accordingly if existing state
   */
  useEffect(() => {
    if (recipientType === "direct-recipient") {
      setTableName("station_direct_recipient");
    } else if (recipientType === "sub-recipient") {
      setTableName("station_sub_recipient");
    } else if (recipientType === "joet") {
      setTableName("station_joet");
    }
  }, []);

  /**
   * Update success banner accordingly if existing state
   */
  useEffect(() => {
    if (state) {
      if (state.createSuccess) {
        setCreateSuccessBanner(true);
        handleCreateSuccessBannerLanguage(state);
      }
      if (state.updateSuccess) {
        setUpdateSuccessBanner(true);
      }
      if (state.rejectSuccess) {
        setRejectSuccessBanner(true)
        handleCreateRejectBannerLanguage(state);
      }
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }, []);

  /**
   * Handle the language for success on station creation
   * @param state the state passed to the route
   * @returns null
   */
  function handleCreateSuccessBannerLanguage(state: any) {
    if (isSRUser()) {
      setSuccessBannerLanugageOnStationCreation(
        `${state.drName} will be notified by email that the station requires their review and approval to be added to EV-ChART. Once approved and added, you may submit data for this station.`,
      );
      return;
    }
    if (state.authorizedSrNamesList.length === 0) {
      setSuccessBannerLanugageOnStationCreation(
        "This station was successfully created and can now be associated with submitted data.",
      );
    } else if (state.authorizedSrNamesList.length === 1) {
      setSuccessBannerLanugageOnStationCreation(
        `${state.authorizedSrNamesList[0]} will be notified by email that they are authorized to submit data for this station on behalf of ${state.drName}.`,
      );
    } else if (state.authorizedSrNamesList.length === 2) {
      setSuccessBannerLanugageOnStationCreation(
        `${state.authorizedSrNamesList[0]} and ${state.authorizedSrNamesList[1]} will be notified by email that they are authorized to submit data for this station on behalf of ${state.drName}.`,
      );
    } else {
      const firstSrNames = state.authorizedSrNamesList.slice(0, -1).join(", ");
      const lastSrName = state.authorizedSrNamesList[state.authorizedSrNamesList.length - 1];
      setSuccessBannerLanugageOnStationCreation(
        `${firstSrNames}, and ${lastSrName} will be notified by email that they are authorized to submit data for this station on behalf of ${state.drName}.`,
      );
    }
  }

/**
   * Handle the language for reject on station creation
   * @param state the state passed to the route
   * @returns null
   */
  function handleCreateRejectBannerLanguage(state: any) {
    if (state.authorizedSrNamesList.length === 0) {
      setRejectBannerLanugage(
        "The station has been rejected and is not added to EV-ChART.",
      );
    } else if (state.authorizedSrNamesList.length === 1) {
      setRejectBannerLanugage(
        `${state.authorizedSrNamesList[0]} will be notified by email that the station has been rejected and is not added to EV-ChART.`,
      );
    } else if (state.authorizedSrNamesList.length === 2) {
      setRejectBannerLanugage(
        `${state.authorizedSrNamesList[0]} and ${state.authorizedSrNamesList[1]}  will be notified by email that the station has been rejected and is not added to EV-ChART.`,
      );
    } else {
      const firstSrNames = state.authorizedSrNamesList.slice(0, -1).join(", ");
      const lastSrName = state.authorizedSrNamesList[state.authorizedSrNamesList.length - 1];
      setRejectBannerLanugage(
        `${firstSrNames}, and ${lastSrName}  will be notified by email that the station has been rejected and is not added to EV-ChART.`,
      );
    }
  }

  /**
   * Page breadcrumb
   * @returns the breadcrumb for the page
   */
  const DefaultBreadcrumb = (): React.ReactElement => (
    <BreadcrumbBar>
      <Breadcrumb>
        <BreadcrumbLink href={ROUTE_HOME}>
          <span>Home</span>
        </BreadcrumbLink>
      </Breadcrumb>
      <Breadcrumb current>
        <span>Stations</span>
      </Breadcrumb>
    </BreadcrumbBar>
  );

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
                <h1> Stations </h1>
              </Grid>
              {(recipientType === "direct-recipient" ||
                (SRAddsStationFeatureFlag && recipientType === "sub-recipient")) &&
                isAdmin() && (
                  <Grid col={2} className="add-station-button">
                    <Button type="button" onClick={() => navigate(ROUTE_STATION_REGISTRATION)}>
                      Add Station
                    </Button>
                  </Grid>
                )}
            </Grid>

            {addSROrgFeatureFlag && recipientType === "direct-recipient" && isAdmin() && (
              <Grid row>
                <Grid className="add-sr-org-text">
                  <p>
                    {" "}
                    Are you using a subrecipient/contractor to submit data, but are unsure if they have access to
                    EV-ChART?{" "}
                    <a className="evchart-link" href={ROUTE_ADD_SR_ORG}>
                      Check for existing organizations or add a new organization.
                    </a>
                  </p>
                </Grid>
              </Grid>
            )}

            {createSuccessBanner && (
              <Alert
                type="success"
                headingLevel="h3"
                className="station-success-banner"
                heading={isDRUser() ? "Station created successfully" : "Station submitted for review successfully"}
              >
                {successBannerLanugageOnStationCreation}
              </Alert>
            )}

            {rejectSuccessBanner && (
              <Alert
                type="success"
                headingLevel="h3"
                className="station-success-banner"
                heading="Station rejected successfully and not added to EV-ChART"
              >
                {rejectBannerLanugage}
              </Alert>
            )}

            {removeSuccessBanner && (
              <Alert
                type="success"
                headingLevel="h3"
                className="station-success-banner"
                heading="Station removed successfully"
              >
                This station has been permanently removed from EV-ChART. Please notify any organization members or
                subrecipients/contractors that need to be made aware of this stations removal.
              </Alert>
            )}

            {updateSuccessBanner && (
              <Alert
                type="success"
                headingLevel="h3"
                className="station-success-banner"
                heading="Station updated successfully"
              >
                This station was successfully updated.
              </Alert>
            )}

            <Grid row>
              <Grid col={12}>
                <h2 className="all-stations-heading"> All Stations </h2>
              </Grid>
            </Grid>
            <StationSummary
              setColumnDefinitionsModal={openColumnDefinitionsModal}
              setStationToRemove={setStationToBeRemoved}
              setRemoveStationModal={openRemoveStationModal}
            />
            {isColumnDefinitionsModalOpen && (
              <ColumnDefinitionsModal table_name={tableName} onClose={closeColumnDefinitionsModal} />
            )}
            {isRemoveStationModalOpen && (
              <RemoveStationModal
                nickname={removedStation.nickname}
                station_id={removedStation.station_id}
                station_uuid={removedStation.station_uuid}
                setSuccessRemove={setBannerRemoveStation}
                onClose={closeRemoveStationModal}
              />
            )}
          </GridContainer>
        </div>
      </div>
    </div>
  );
}

export default Stations;
