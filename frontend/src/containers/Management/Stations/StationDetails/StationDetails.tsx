/**
 * Displays station details.
 * @packageDocumentation
 **/
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import { useLocation } from "react-router-dom";

import {
  Breadcrumb,
  BreadcrumbBar,
  BreadcrumbLink,
  Button,
  Chip,
  GridContainer,
  Grid,
  Icon,
  Tooltip,
  Spinner,
  ErrorMessage,
  Label,
  ComboBox,
} from "evchartstorybook";

import { projectTypeMapping, stateCodeMapping } from "../../../../interfaces/Stations/station-form-options";
import { StationDetailsViewOnly } from "../../../../interfaces/Stations/stations-interface";
import { OrganizationSummary, NetworkProviderInfo } from "interfaces/Organization/organizations-interface";

import { isAdmin, isDRUser, isJOUser, isSRUser } from "../../../../utils/authFunctions";
import { getOrgID, getOrgName } from "../../../../utils/getJWTInfo";
import {
  PATH_NETWORK_PROVIDERS,
  PATH_STATION_ID,
  PATH_STATIONS,
  PATH_SUB_RECIPIENTS,
} from "../../../../utils/pathConstants";
import { FeatureFlagEnum, getFeatureFlagList, getFeatureFlagValue } from "../../../../utils/FeatureToggle";

import {
  ROUTE_AUTHROIZE_CONTRACTORS,
  ROUTE_EDIT,
  ROUTE_HOME,
  ROUTE_NOT_AUTHORIZED,
  ROUTE_NOT_FOUND,
  ROUTE_STATION_ID,
  ROUTE_STATIONS,
} from "../../../../utils/routeConstants";

import RejectModal from "../../../../components/Modals/RejectStationModal/RejectModal";
import CustomLink from "../../../../components/Tooltip/tooltips";

import "../StationDetails/StationDetails.css";
import "../StationForm/StationForm.css";

function StationDetails() {
  /**
   * Method for changing the location / route
   */
  const location = useLocation();
  const navigate = useNavigate();

  /**
   * Get the api and base url from the environment variables
   */
  const BASE_URL = import.meta.env.VITE_PUBLIC_URL;
  const API_URL = import.meta.env.VITE_API_URL;

  /**
   * Get id token for endpoint authorization
   */
  const id_token = localStorage.getItem("id_token");

  /**
   * Feature flag management
   */
  const [nTierFeatureFlag, setNTierFeatureFlag] = useState<boolean | null>(null);
  const [RegisterNonFedFundedStationFeatureFlag, setRegisterNonFedFundedStationFeatureFlag] = useState(false);
  useEffect(() => {
    getFeatureFlagList().then((results) => {
      setNTierFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.NTierOrganizations));
      setRegisterNonFedFundedStationFeatureFlag(
        getFeatureFlagValue(results, FeatureFlagEnum.RegisterNonFedFundedStation),
      );
    });
  }, []);
  const [isAuthorizeSubcontractorsView, setIsAuthorizeSubcontractorsView] = useState(false);

  /**
   * Redirect to not authorized if attempting to authorize contractors and FF is off
   */
  useEffect(() => {
    if (isAuthorizeSubcontractorsView && nTierFeatureFlag === false) {
      navigate(ROUTE_NOT_FOUND);
    }
  }, [isAuthorizeSubcontractorsView]);

  /**
   * When data is uploading show spinner
   **/
  const [isUploadingData, setIsUploadingData] = useState<boolean>(false);

  /**
   * Get the uuid of the current station from the path
   */
  const [station_uuid, setStationUuid] = useState<string>("");
  useEffect(() => {
    // Split the url to see the station id
    const urlParts = window.location.href.split("/");
    // Get the station id of the url to load
    if (urlParts[7] === "authorize-contractors") {
      setStationUuid(urlParts[urlParts.length - 2]);
      setIsAuthorizeSubcontractorsView(true);
    } else {
      setStationUuid(urlParts[urlParts.length - 1]);
      setIsAuthorizeSubcontractorsView(false);
    }
  }, [location.pathname]);

  /**
   * Setting org info for the API Call
   */
  const [orgId, setOrgID] = useState("");
  useEffect(() => {
    const jwtOrgID = getOrgID();
    if (jwtOrgID) {
      setOrgID(jwtOrgID);
    }
  }, []);

  /**
   * Values for view only station info
   */
  const [stationValues, setStateValues] = useState<StationDetailsViewOnly>({
    station_uuid: "",
    address: "",
    city: "",
    project_type: "",
    station_id: "",
    latitude: "",
    longitude: "",
    nickname: "",
    num_fed_funded_ports: "",
    num_non_fed_funded_ports: "",
    state: "",
    status: "",
    network_provider: "",
    operational_date: "",
    NEVI: 0,
    CFI: 0,
    EVC_RAA: 0,
    CMAQ: 0,
    CRP: 0,
    OTHER: 0,
    AFC: 0,
    authorized_subrecipients: [],
    zip: "",
    zip_extended: "",
    fed_funded_ports: [],
    non_fed_funded_ports: [],
  });

  /**
   * State variables
   */
  const [networkProviders, setNetworkProviders] = useState<NetworkProviderInfo[]>([]);
  const [isStationPending, setIsStationPending] = useState<boolean | null>(null);
  const [isSpinnerRendered, setIsSpinnerRendered] = useState(true);
  const [isStationApproved, setIsStationApproved] = useState(false);
  const [isNPDataLoading, setIsNPDataLoading] = useState(true);
  const [isRejectStationModalOpen, setIsRejectStationModalOpen] = useState(false);
  const [isFederallyFunded, setIsFederallyFunded] = useState<boolean>();

  /**
   * Open and close the station reject modal
   */
  const openRejectStationModal = () => {
    setIsRejectStationModalOpen(true);
  };
  const closeRejectStationModal = () => {
    setIsRejectStationModalOpen(false);
  };

  /**
   * Get the station information from API
   */
  useEffect(() => {
    if (orgId) {
      fetch(`${API_URL}${PATH_STATION_ID}?station_uuid=${station_uuid}`, {
        method: "GET",
        headers: {
          Authorization: `${id_token}`,
        },
      })
        .then((response) => {
          if (response.ok) {
            return response.json();
          } else {
            throw response;
          }
        })
        .then((data) => {
          setStateValues(data);
          updateField("nickname", data.nickname);
          setIsFederallyFunded(Boolean(data.num_fed_funded_ports >= 1));
          updateField("operational_date", convertDateFormat(data.operational_date));

          if (data.status === "Pending Approval") {
            setIsStationPending(true);
          } else {
            setIsStationPending(false);
          }
          if (data.authorized_subrecipients && data.authorized_subrecipients !== "") {
            updateSRMapping(data.authorized_subrecipients);
          }
          if (networkProviders) {
            const stationNetworkProvider = networkProviders.find(
              (item) => item.network_provider_value === data.network_provider,
            );
            updateField("network_provider", stationNetworkProvider?.description);
          }
          window.scrollTo({ top: 0, behavior: "smooth" });
        })
        .catch((err) => {
          const errorCode = err.status;

          if (errorCode === 403) {
            navigate(ROUTE_NOT_AUTHORIZED);
          }
          if (errorCode === 406) {
            navigate(ROUTE_NOT_FOUND);
          }
        })
        .finally(() => setIsSpinnerRendered(false));
    }
  }, [orgId, networkProviders]);

  /**
   * Format the returned SRs from the API to render on the page
   * @param sr_object the object returned from the api
   */
  function updateSRMapping(sr_object: any) {
    const comboBoxIds = Array.from({ length: Object.keys(sr_object).length }, () =>
      Number(Math.floor(Math.random() * 100_000_000)),
    );
    setAuthorizeSubrecipients(comboBoxIds);
    setSelectedSubrecipients(Object.keys(sr_object));
    setOriginalSubrecipients(Object.keys(sr_object));
    updateField("authorized_subrecipients", Object.keys(sr_object));
  }

  /**
   * Get the network providers
   */
  useEffect(() => {
    fetch(`${API_URL}${PATH_NETWORK_PROVIDERS}`, {
      method: "GET",
      headers: {
        Authorization: `${id_token}`,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        setNetworkProviders(data);
      })
      .catch((err) => {
        console.log(err.message);
      })
      .finally(() => setIsNPDataLoading(false));
  }, []);

  /**
   * Function to iterate through the station object and determine which funding
   * recipients were indicated during station registration
   * @param obj the station information
   * @returns an array with all the funding recipients found
   */
  function getSelectedFundingRecipients(obj: any) {
    const keysToCheck = ["NEVI", "CFI", "EVC_RAA", "CMAQ", "CRP", "OTHER"];

    const selectedKeys = [];

    for (const key of keysToCheck) {
      if (obj[key] === 1) selectedKeys.push(key);
    }
    return selectedKeys.join(", ");
  }

  /**
   * Function to format date
   * @param dateString the date string returned from the api
   * @returns the formatted date
   */
  function convertDateFormat(dateString: string): string {
    const [year, month, day] = dateString.split("-");
    const formattedDate = `${month}/${day}/${year}`;
    return formattedDate;
  }

  /**
   * Function to update fields
   * @param fieldName the field to be updated
   * @param value the value to update it to
   */
  const updateField = (fieldName: string, value: any) => {
    setStateValues((prevState) => ({
      ...prevState,
      [fieldName]: value,
    }));
  };

  /**
   * Event tied to station approval
   */
  const handleApproveStation = () => {
    setIsStationApproved(true);
    const access_token = localStorage.getItem("access_token");
    const approveStation = {
      station_uuid: station_uuid,
      status: "Active",
      federally_funded: isFederallyFunded,
    };
    setIsUploadingData(true);

    fetch(`${API_URL}${PATH_STATIONS}`, {
      method: "PATCH",
      headers: {
        Authorization: `${access_token}`,
      },
      body: JSON.stringify(approveStation),
    })
      .then((response) => {
        if (response.ok) {
          navigate(ROUTE_STATIONS, {
            state: {
              createSuccess: true,
              authorizedSrNamesList: getAuthorizedSrNamesByOrgId(),
              drName: getOrgName(),
            },
          });
        } else {
          throw response;
        }
      })
      .catch((err) => {
        console.log(err);
      })
      .finally(() => {
        setIsUploadingData(false);
      });
  };

  /**
   * Open rejection modal
   */
  const handleRejectStation = () => {
    openRejectStationModal();
  };

  /**
   * State variables to manage authorization of contractors by SRs
   */
  const [errorSubrecipients, setErrorSubrecipients] = useState<number[]>([]);
  const [authorizeSubrecipients, setAuthorizeSubrecipients] = useState<number[]>([]);
  const [originalSubrecipients, setOriginalSubrecipients] = useState<string[]>([]);

  /**
   * The options returned from the /org/subrecipients endpoint for use in the combobox
   * for direct recipients authorizing subrecipients
   */
  const [subrecipientOptions, setSubrecipientOptions] = useState<OrganizationSummary[]>([
    {
      org_id: "",
      recipient_type: "",
      name: "",
      org_friendly_id: "",
    },
  ]);

  /**
   * The subrecipient options converted to a list for use within the combobox component
   * Label is a concatenation of the organization name and the friendly id
   */
  const subRecipientsList = subrecipientOptions?.map(
    (item: { org_id: string; name: string; org_friendly_id: string }) => ({
      value: item.org_id,
      label: `${item.name} - ${item.org_friendly_id}`,
    }),
  );

  /**
   * Check if subrecipient contain errors, and return appropriate class name to highlight field
   * @param num the combobox index being checked
   * @returns the class name
   */
  const checkEntriesError = (num: number) => {
    if (errorSubrecipients.includes(num)) {
      return "error-combobox";
    } else {
      return "";
    }
  };

  /**
   * State variable to keep track of the subrecipients a user has selected
   */
  const [selectedSubrecipients, setSelectedSubrecipients] = useState<string[]>([]);

  /**
   * If in edit mode, get the "default" value for the combobox based on the id
   * @param index which subrecipient should be populated in the combobox
   * @returns the org_id of the subrecipient
   */
  function getSubRecipientComboboxDefaultValue(index: number) {
    return stationValues.authorized_subrecipients[index];
  }

  /**
   * Event tied to user updating the combobox (by typing or scrolling through the list)
   * @param value the org_id for the subrecipient
   * @param index the index of the combobox
   * @param subRecipientComboboxId the id for the combobox
   */
  const handleComboBoxChange = (value: any, index: number, subRecipientComboboxId: number) => {
    const newSelectedSubrecipients = [...selectedSubrecipients];
    newSelectedSubrecipients[index] = value;
    setSelectedSubrecipients(newSelectedSubrecipients);
    updateField("authorized_subrecipients", newSelectedSubrecipients);
    setErrorSubrecipients(errorSubrecipients.filter((id) => id !== subRecipientComboboxId));
  };

  /**
   * Event tied to "Remove" next to subrecipient name
   * Removes the combobox entirely from the UI and the users selection
   * @param subRecipientComboboxId the combobox to remove
   */
  const handleRemoveSubrecipient = (subRecipientComboboxId: number) => {
    setAuthorizeSubrecipients(authorizeSubrecipients.filter((id) => id !== subRecipientComboboxId));
    const newSelectedSubrecipients = [...selectedSubrecipients];
    const indexToRemove = authorizeSubrecipients.indexOf(subRecipientComboboxId);
    if (indexToRemove !== -1) {
      newSelectedSubrecipients.splice(indexToRemove, 1);
      setSelectedSubrecipients(newSelectedSubrecipients);
      updateField("authorized_subrecipients", newSelectedSubrecipients);
    }
    setErrorSubrecipients(errorSubrecipients.filter((id) => id !== subRecipientComboboxId));
  };

  /**
   * Event tied to "Add Subrecipient"
   * Creates a new empty combobox for the user to make a new selection for subrecipients
   */
  const handleAddSubrecipient = () => {
    const newSubRecipientId = Math.floor(Math.random() * 100_000_000);
    setAuthorizeSubrecipients([...authorizeSubrecipients, newSubRecipientId]);
    setSelectedSubrecipients([...selectedSubrecipients, ""]);
  };

  /**
   * getting list of all drs or srs for step 2 dependin on user's recipient type
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
        setSubrecipientOptions(data);
      })
      .catch((err) => {
        console.log(err.message);
      });
  }, []);

  interface EditedStationValues {
    srs_removed?: string[];
    srs_added?: string[];
  }

  /**
   * Handle saving station for authorizing contractors
   */
  const handleSaveStation = () => {
    const authorizeContractorsStation: EditedStationValues = {};

    // contractor Added
    const srs_added = selectedSubrecipients.filter((uuid) => !originalSubrecipients.includes(uuid));
    if (srs_added.length !== 0) {
      authorizeContractorsStation.srs_added = srs_added;
    }

    // contractor Removed
    const srs_removed = originalSubrecipients.filter((uuid) => !selectedSubrecipients.includes(uuid));
    if (srs_removed.length !== 0) {
      authorizeContractorsStation.srs_removed = srs_removed;
    }
  };

  /**
   * Form to authorize contractors
   * @returns the contractor authorization section
   */
  function SRAuthorizesContractorsForm(): React.ReactNode {
    return (
      <>
        <Grid row col={8}>
          <p>
            Contractors may be authorized by you, the Subrecipient organization, to view/submit data for a specific
            station. Only Subrecipient Administrators can authorize Contractors to submit data on their behalf.
          </p>
        </Grid>
        {errorSubrecipients.length > 0 && (
          <Grid row col={8} style={{ marginTop: 15 }}>
            <ErrorMessage>Please make a unique selection for each entry or remove the dropdown.</ErrorMessage>
          </Grid>
        )}

        <Grid>
          {authorizeSubrecipients.map((subRecipientComboboxId, index) => (
            <Grid className="organization-selection-combobox" key={subRecipientComboboxId}>
              <Grid row>
                <Grid col={5}>
                  <Label htmlFor="subrecipient" className="required-field">
                    Authorize Contractor
                  </Label>
                  <ComboBox
                    id={`input-subrecipient${subRecipientComboboxId}`}
                    name={`input-subrecipient${subRecipientComboboxId}`}
                    options={subRecipientsList}
                    className={checkEntriesError(subRecipientComboboxId)}
                    defaultValue={getSubRecipientComboboxDefaultValue(index)}
                    onChange={(value) => handleComboBoxChange(value, index, subRecipientComboboxId)}
                  />
                </Grid>
                <Grid>
                  <Button
                    type="button"
                    unstyled
                    className="remove-button padding-105 text-center"
                    onClick={() => handleRemoveSubrecipient(subRecipientComboboxId)}
                  >
                    Remove
                  </Button>
                </Grid>
              </Grid>
            </Grid>
          ))}
          <Button outline className="form-add-button" type="button" onClick={handleAddSubrecipient}>
            Add Subrecipient
          </Button>
        </Grid>
      </>
    );
  }

  /**
   * Function to get SR names from their org IDs
   * @returns the subrecipient names
   */
  const getAuthorizedSrNamesByOrgId = () => {
    const srNames = stationValues.authorized_subrecipients
      .map((sr_id) => {
        const org_id = subrecipientOptions.find((org) => org.org_id === sr_id);
        return org_id ? org_id.name : null;
      })
      .filter((sr_id): sr_id is string => sr_id != null);
    return srNames;
  };

  /**
   * Function to render the SRs authorized to a station
   * @returns the list of all contractors/ SRs authorized
   */
  function AuthorizedToStationList(): React.ReactNode {
    return (
      <>
        {getAuthorizedSrNamesByOrgId().map((subrecipient, index) => (
          <Grid
            key={subrecipient}
            row
            className={
              index + 1 === Object.keys(stationValues.authorized_subrecipients).length
                ? "station-details-field"
                : "station-details-field station-details-underline"
            }
          >
            <Grid col={12}>
              <p className="station-details-value">{subrecipient}</p>
            </Grid>
          </Grid>
        ))}
      </>
    );
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
      <Breadcrumb>
        <BreadcrumbLink href={`${BASE_URL}${ROUTE_STATIONS}`}>
          <span>Stations</span>
        </BreadcrumbLink>
      </Breadcrumb>
      <Breadcrumb current>
        <span>{isAuthorizeSubcontractorsView ? "Edit Station" : "Station Details"}</span>
      </Breadcrumb>
    </BreadcrumbBar>
  );

  /**
   * Set width for the cards and fields
   */
  const cardWidth = 12;
  const labelWidth = 3;
  const valueWidth = 7;

  return (
    <>
      <div className="stationRegistration stationDetails">
        <div>
          <GridContainer>
            <DefaultBreadcrumb />
          </GridContainer>
        </div>
        <div className="usa-section" style={{ paddingTop: 0 }}>
          <GridContainer className="station-card-container">
            <Grid row>
              <Grid col={8}>
                <h1 className="station-details-page-header">
                  {isAuthorizeSubcontractorsView ? "Edit Station" : "Station Details"}
                </h1>
              </Grid>
              {isStationPending !== null && isDRUser() && isAdmin() && (
                <Grid col={4}>
                  <Button
                    type="button"
                    className="station-edit-button"
                    onClick={() => navigate(`${ROUTE_STATION_ID}/${station_uuid}${ROUTE_EDIT}`)}
                  >
                    {isStationPending ? "Edit Station Details" : "Edit"}
                  </Button>
                </Grid>
              )}
              {nTierFeatureFlag && isSRUser() && !isAuthorizeSubcontractorsView && (
                <Grid col={4}>
                  <Button
                    type="button"
                    className="station-edit-button"
                    onClick={() => navigate(`${ROUTE_STATION_ID}/${station_uuid}${ROUTE_AUTHROIZE_CONTRACTORS}`)}
                  >
                    Authorize Contractors
                  </Button>
                </Grid>
              )}
            </Grid>
          </GridContainer>

          {(isSpinnerRendered && isNPDataLoading) || isStationApproved || isUploadingData ? (
            <div className="pp-dashboard-spinner-container">
              <div className="pp-dashboard-spinner">
                <Spinner />
              </div>
            </div>
          ) : (
            <>
              <GridContainer className="station-card-container">
                <Grid row>
                  <Grid col={12} className="station-details-card">
                    <GridContainer className="station-card-content">
                      <Grid row className="station-details-underline">
                        <Grid row col={cardWidth}>
                          <div className="station-header">
                            {isAuthorizeSubcontractorsView && "Step 1: "}Station Profile
                          </div>
                        </Grid>
                      </Grid>
                      <Grid row className="station-details-field station-details-underline">
                        <Grid col={labelWidth}>
                          <div className="label-tooltip-container">
                            <span>Station Nickname:</span>
                            <Tooltip
                              label={
                                isDRUser()
                                  ? "Station Nickname was created by a user within your organization, it should be easy to remember and be used to distinguish this station from others."
                                  : "The Station Nickname was given to the station by the Direct Recipient organization upon station registration."
                              }
                              asCustom={CustomLink}
                              className="station-details-tooltip"
                            >
                              <Icon.InfoOutline className="tooltip-icon" />
                            </Tooltip>
                          </div>
                        </Grid>
                        <Grid col={valueWidth}>
                          <p className="station-details-value">
                            {stationValues.nickname ? stationValues.nickname : ""}
                          </p>
                        </Grid>
                      </Grid>
                      <Grid row className="station-details-field station-details-underline">
                        <Grid col={labelWidth}>
                          <div className="label-tooltip-container">
                            <span>Station ID:</span>
                            <Tooltip
                              label={
                                "This uniquely identifies a charging station. This should have been created by the Network Provider and per 23 CFR 680.112, this must be the same charging station identifier used to identify the charging station in data made available to third-parties in 23 CFR 680.116(c)(1)."
                              }
                              asCustom={CustomLink}
                            >
                              <Icon.InfoOutline className="tooltip-icon" />
                            </Tooltip>
                          </div>
                        </Grid>
                        <Grid col={valueWidth}>
                          <p className="station-details-value">{stationValues.station_id}</p>
                        </Grid>
                      </Grid>
                      <Grid row className="station-details-field station-details-underline">
                        <Grid col={labelWidth}>
                          <span>Station Address:</span>
                        </Grid>
                        <Grid col={valueWidth}>
                          <p className="station-details-value">{stationValues.address}</p>
                        </Grid>
                      </Grid>
                      <Grid row className="station-details-field station-details-underline">
                        <Grid col={labelWidth}>
                          <span>Station City:</span>
                        </Grid>
                        <Grid col={valueWidth}>
                          <p className="station-details-value">{stationValues.city}</p>
                        </Grid>
                      </Grid>
                      <Grid row className="station-details-field station-details-underline">
                        <Grid col={labelWidth}>
                          <span>Station State:</span>
                        </Grid>
                        <Grid col={valueWidth}>
                          <p className="station-details-value">{stateCodeMapping(stationValues.state.toLowerCase())}</p>
                        </Grid>
                      </Grid>
                      <Grid row className="station-details-field station-details-underline">
                        <Grid col={labelWidth}>
                          <span>Station ZIP:</span>
                        </Grid>
                        <Grid col={valueWidth}>
                          <p className="station-details-value">{stationValues.zip}</p>
                        </Grid>
                      </Grid>
                      <Grid row className="station-details-field station-details-underline">
                        <Grid col={labelWidth}>
                          <span>Station ZIP Extended:</span>
                        </Grid>
                        <Grid col={valueWidth}>
                          <p className="station-details-value">{stationValues.zip_extended}</p>
                        </Grid>
                      </Grid>
                      <Grid row className="station-details-field station-details-underline">
                        <Grid col={labelWidth}>
                          <span>Station Latitude:</span>
                        </Grid>
                        <Grid col={valueWidth}>
                          <p className="station-details-value">{stationValues.latitude}</p>
                        </Grid>
                      </Grid>
                      <Grid row className="station-details-field station-details-underline">
                        <Grid col={labelWidth}>
                          <span>Station Longitude:</span>
                        </Grid>
                        <Grid col={valueWidth}>
                          <p className="station-details-value">{stationValues.longitude}</p>
                        </Grid>
                      </Grid>

                      {!RegisterNonFedFundedStationFeatureFlag && (
                        <Grid row className="station-details-field station-details-underline">
                          <Grid col={labelWidth}>
                            <div className="label-tooltip-container">
                              <span>Project Type:</span>
                              <Tooltip
                                label={`The Project Type describes how the federal funds are being spent. "Install a New Station" is for any station that was newly built using federal funds. "Update an existing station" is for any station that already existed but used federal funds to be repaired, replaced, or upgraded to be compliant. "Only Provide O&M" is for any station where federal funds are only used for operation and maintenance.`}
                                asCustom={CustomLink}
                              >
                                <Icon.InfoOutline className="tooltip-icon" />
                              </Tooltip>
                            </div>
                          </Grid>
                          <Grid col={valueWidth}>
                            <p className="station-details-value">{projectTypeMapping(stationValues.project_type)}</p>
                          </Grid>
                        </Grid>
                      )}

                      <Grid row className="station-details-field station-details-underline">
                        <Grid col={labelWidth}>
                          <div className="label-tooltip-container">
                            <span>Network Provider:</span>
                            <Tooltip
                              label={`The Network Provider is the entity that operates the digital communication network that remotely manages the chargers. Charging network providers may also serve as charging station operators and/or manufacture chargers.`}
                              asCustom={CustomLink}
                            >
                              <Icon.InfoOutline className="tooltip-icon" />
                            </Tooltip>
                          </div>
                        </Grid>
                        <Grid col={valueWidth}>
                          <p className="station-details-value">{stationValues.network_provider}</p>
                        </Grid>
                      </Grid>

                      <Grid row className="station-details-field station-details-underline">
                        <Grid col={labelWidth}>
                          <span>Station Status:</span>
                        </Grid>
                        <Grid col={valueWidth}>
                          {isStationPending ? (
                            <Chip type="warning">Pending Approval</Chip>
                          ) : (
                            <Chip type="success">Active</Chip>
                          )}
                        </Grid>
                      </Grid>

                      <Grid row className="station-details-field station-details-underline">
                        <Grid col={labelWidth}>
                          <span>Operational Date:</span>
                        </Grid>
                        <Grid col={valueWidth}>
                          <p className="station-details-value">{stationValues.operational_date}</p>
                        </Grid>
                      </Grid>

                      {!RegisterNonFedFundedStationFeatureFlag && isFederallyFunded && (
                        <Grid row className="station-details-field station-details-underline">
                          <Grid col={labelWidth}>
                            <span>Funding Type:</span>
                          </Grid>
                          <Grid col={valueWidth}>
                            <p className="station-details-value">{getSelectedFundingRecipients(stationValues)}</p>
                          </Grid>
                        </Grid>
                      )}

                      <Grid row className="station-details-field ">
                        <Grid col={labelWidth}>
                          <span>Station Located on AFC:</span>
                        </Grid>
                        <Grid col={valueWidth}>
                          <p className="station-details-value">{stationValues.AFC === 1 ? "Yes" : "No"}</p>
                        </Grid>
                      </Grid>
                    </GridContainer>
                  </Grid>
                </Grid>
              </GridContainer>

              {RegisterNonFedFundedStationFeatureFlag && (
                <GridContainer className="station-card-container">
                  <Grid col={cardWidth} className="station-details-card">
                    <GridContainer className="station-card-content">
                      <Grid row className="station-details-underline">
                        <Grid row col={cardWidth}>
                          <div className="station-header">Federal Funding Status</div>
                        </Grid>
                      </Grid>
                      <Grid row className="station-details-field station-details-underline">
                        <Grid col={labelWidth}>
                          <div className="label-tooltip-container">
                            <span>Federally Funded:</span>
                            <Tooltip
                              label={`The acquisition, installation, network connection, operation, or maintenance of this charging station, uses NEVI Formula Program funds, funds made available under Title 23, U.S.C. for projects for the construction of publicly accessible EV chargers, or any EV charging infrastructure project funded with Federal funds that is treated as a project on a Federal-aid highway.`}
                              asCustom={CustomLink}
                            >
                              <Icon.InfoOutline className="tooltip-icon" />
                            </Tooltip>
                          </div>
                        </Grid>
                        <Grid col={valueWidth}>
                          <p className="station-details-value">
                            {Number(stationValues.num_fed_funded_ports) > 0 ? "Yes" : "No"}
                          </p>
                        </Grid>
                      </Grid>

                      {isFederallyFunded && (
                        <Grid row className="station-details-field station-details-underline">
                          <Grid col={labelWidth}>
                            <span>Funding Type:</span>
                          </Grid>
                          <Grid col={valueWidth}>
                            <p className="station-details-value">{getSelectedFundingRecipients(stationValues)}</p>
                          </Grid>
                        </Grid>
                      )}
                      <Grid row className="station-details-field">
                        <Grid col={labelWidth}>
                          <div className="label-tooltip-container">
                            <span>Project Type:</span>
                            <Tooltip
                              label={`The Project Type describes how the federal funds are being spent. "Install a New Station" is for any station that was newly built using federal funds. "Update an existing station" is for any station that already existed but used federal funds to be repaired, replaced, or upgraded to be compliant. "Only Provide O&M" is for any station where federal funds are only used for operation and maintenance.`}
                              asCustom={CustomLink}
                            >
                              <Icon.InfoOutline className="tooltip-icon" />
                            </Tooltip>
                          </div>
                        </Grid>
                        <Grid col={valueWidth}>
                          <p className="station-details-value">{projectTypeMapping(stationValues.project_type)}</p>
                        </Grid>
                      </Grid>
                    </GridContainer>
                  </Grid>
                </GridContainer>
              )}

              {(isDRUser() || isJOUser()) && (
                <GridContainer className="station-card-container">
                  <Grid row>
                    <Grid col={cardWidth} className="station-details-card">
                      <GridContainer className="station-card-content">
                        <Grid row className="station-details-underline">
                          <Grid col={12}>
                            <div className="station-header">Subrecipients/Contractors</div>
                          </Grid>
                        </Grid>
                        {stationValues.authorized_subrecipients.length === 0 ? (
                          <Grid row className="station-details-field station-details-underline">
                            <Grid col={12}>
                              <div className="station-details-field no-authorized-subrecipients-text">
                                No subrecipients have been authorized for this station.
                              </div>
                            </Grid>
                          </Grid>
                        ) : (
                          AuthorizedToStationList()
                        )}
                      </GridContainer>
                    </Grid>
                  </Grid>
                </GridContainer>
              )}

              {nTierFeatureFlag && isSRUser() && (
                <GridContainer className="station-card-container">
                  <Grid col={cardWidth} className="station-details-card">
                    <GridContainer className="station-card-content">
                      <Grid row className="station-details-underline">
                        <div className="station-header">
                          {isAuthorizeSubcontractorsView ? "Step 2: Authorize Contractors" : "Contractors"}
                        </div>
                      </Grid>
                      {isAuthorizeSubcontractorsView ? SRAuthorizesContractorsForm() : AuthorizedToStationList()}
                    </GridContainer>
                  </Grid>
                </GridContainer>
              )}

              <GridContainer className="station-card-container">
                <Grid col={cardWidth} className="station-details-card">
                  <GridContainer className="station-card-content">
                    <Grid row className="station-details-underline">
                      <div className="station-header">
                        {" "}
                        {isAuthorizeSubcontractorsView && "Step 3: "}Port Information
                      </div>
                    </Grid>
                    <Grid row gap id="noPortsField" className="station-details-field">
                      <Grid id="noPortsContainer">
                        <div>Number of Federally Funded Ports:</div>
                        <div id="noPortsValue">
                          <p className="station-details-value">{stationValues.num_fed_funded_ports}</p>
                        </div>
                      </Grid>
                    </Grid>

                    {stationValues.fed_funded_ports.length > 0 && (
                      <>
                        <Grid row gap id="noPortsField" className="station-details-field">
                          <Grid col={6} id="noPortsContainer">
                            <div>Port ID:</div>
                          </Grid>
                          <Grid col={6} id="noPortsContainer">
                            <div>Port Type:</div>
                          </Grid>
                        </Grid>
                        {stationValues.fed_funded_ports.map((port) => (
                          <Grid row gap id="noPortsField" className="station-details-field" key={port.port_id}>
                            <Grid col={6}>
                              <div className="station-details-value">{port.port_id}</div>
                            </Grid>
                            <Grid col={6}>
                              <div className="station-details-value">
                                {port.port_type !== "" ? port.port_type : "No Port Type added"}
                              </div>
                            </Grid>
                          </Grid>
                        ))}{" "}
                      </>
                    )}
                    <div id="portCount" className="station-details-field port-summary-top-border">
                      <span>
                        <i>
                          {stationValues.fed_funded_ports.length} Port IDs of {stationValues.num_fed_funded_ports} Ports
                          added
                        </i>
                      </span>
                    </div>

                    <Grid row gap id="noPortsField" className="station-details-field non-fed-ports-container">
                      <Grid id="noPortsContainer">
                        <div>Number of Non-Federally Funded Ports:</div>
                        <div id="noPortsValue">
                          <p className="station-details-value">{stationValues.num_non_fed_funded_ports}</p>
                        </div>
                      </Grid>
                    </Grid>

                    {stationValues.non_fed_funded_ports.length > 0 && (
                      <>
                        <Grid row gap id="noPortsField" className="station-details-field">
                          <Grid col={6} id="noPortsContainer">
                            <div>Port ID:</div>
                          </Grid>
                          <Grid col={6} id="noPortsContainer">
                            <div>Port Type:</div>
                          </Grid>
                        </Grid>
                        {stationValues.non_fed_funded_ports.map((port, index) => (
                          <Grid row gap key={index} id="noPortsField" className="station-details-field">
                            <Grid col={6}>
                              <div className="station-details-value">{port.port_id}</div>
                            </Grid>
                            <Grid col={6}>
                              <div className="station-details-value">
                                {port.port_type !== "" ? port.port_type : "No Port Type added"}
                              </div>
                            </Grid>
                          </Grid>
                        ))}{" "}
                      </>
                    )}

                    <div id="portCount" className="station-details-field port-summary-top-border">
                      <span>
                        <i>
                          {stationValues.non_fed_funded_ports.length} Port IDs of{" "}
                          {stationValues.num_non_fed_funded_ports} Ports added
                        </i>
                      </span>
                    </div>
                  </GridContainer>
                </Grid>
                {isStationPending && isDRUser() && isAdmin() && (
                  <Grid row className="pending-station-button-options">
                    <Button type="button" disabled={isUploadingData} onClick={handleApproveStation}>
                      Approve & Add Station
                    </Button>

                    <Button type="button" disabled={isUploadingData} outline onClick={handleRejectStation}>
                      Reject & Do Not Add Station
                    </Button>

                    <Button
                      type="button"
                      disabled={isUploadingData}
                      unstyled
                      onClick={() => navigate(`${ROUTE_STATIONS}`)}
                    >
                      Cancel
                    </Button>
                  </Grid>
                )}
                {isAuthorizeSubcontractorsView && isSRUser() && isAdmin() && (
                  <Grid row className="pending-station-button-options">
                    <Button type="button" disabled={isUploadingData} onClick={handleSaveStation}>
                      Save
                    </Button>
                    <Button
                      type="button"
                      unstyled
                      disabled={isUploadingData}
                      onClick={() => navigate(`${ROUTE_STATION_ID}/${station_uuid}`)}
                    >
                      Cancel
                    </Button>
                  </Grid>
                )}
              </GridContainer>
            </>
          )}
          {isRejectStationModalOpen && (
            <RejectModal
              onClose={closeRejectStationModal}
              stationUUID={station_uuid}
              authorizedSrNamesList={getAuthorizedSrNamesByOrgId()}
              stationID={stationValues.station_id}
              nickname={stationValues.nickname}
              address={stationValues.address}
              numFederalPorts={stationValues.num_fed_funded_ports}
              numNonFederalPorts={stationValues.num_non_fed_funded_ports}
            />
          )}
        </div>
      </div>
    </>
  );
}

export default StationDetails;
