/**
 * Form to register station location (module 1).
 * @packageDocumentation
 **/
import React, { useState, useEffect, SyntheticEvent, ChangeEvent } from "react";
import { useNavigate } from "react-router";

import {
  Alert,
  Breadcrumb,
  BreadcrumbBar,
  BreadcrumbLink,
  Button,
  ButtonGroup,
  CharacterCount,
  Checkbox,
  ComboBox,
  DatePicker,
  ErrorMessage,
  Fieldset,
  GridContainer,
  Grid,
  Icon,
  Label,
  Radio,
  Select,
  SelectOpt,
  TextInput,
  Tooltip,
  Spinner,
} from "evchartstorybook";

import { OrganizationSummary, NetworkProviderInfo } from "../../../../interfaces/Organization/organizations-interface";
import { states } from "../../../../interfaces/Stations/combobox";
import { EditedStationValues, PortsInfo, StationAddNew } from "../../../../interfaces/Stations/stations-interface";

import { isDRUser } from "../../../../utils/authFunctions";
import { FeatureFlagEnum, getFeatureFlagValue, getFeatureFlagList } from "../../../../utils/FeatureToggle";
import { getOrgID, getOrgName, getScope } from "../../../../utils/getJWTInfo";
import {
  PATH_NETWORK_PROVIDERS,
  PATH_STATION_ID,
  PATH_STATIONS,
  PATH_SUB_RECIPIENTS,
  PATH_DIRECT_RECIPIENTS,
} from "../../../../utils/pathConstants";
import { ROUTE_HOME, ROUTE_NOT_AUTHORIZED, ROUTE_STATIONS } from "../../../../utils/routeConstants";

import FormLabelAndTooltip from "./StationFormLabel";
import CancelModal from "../../../../components/Modals/CancelModal/CancelModal";
import SRAddStationModal from "../../../../components/Modals/SRAddStationModal/SRAddStationModal";
import CustomLink from "../../../../components/Tooltip/tooltips";
import { characterLimits, convertDateFormat, inputValid, checkValidData } from "./StationFormUtils";

import "./StationForm.css";
import RemovePortConfirmationModal from "../../../../components/Modals/RemovePortsConfirmationModal/RemovePortsConfirmation";

/**
 * initial error state - all are false (inputs are assumed to be correct)
 */
const initialErrorState = {
  nickname: false,
  address: false,
  city: false,
  project_type: false,
  network_provider: false,
  station_id: false,
  latitude: false,
  longitude: false,
  num_fed_funded_ports: false,
  num_non_fed_funded_ports: false,
  state: false,
  authorized_subrecipients: false,
  zip: false,
  zip_extended: false,
  fed_funded_ports: false,
  non_fed_funded_ports: false,
  dr_id: false,
};

const InitialCustomErrors = {
  station_id: false,
  latitude: false,
  longitude: false,
  num_fed_funded_ports: false,
  num_non_fed_funded_ports: false,
  zip: false,
  zip_extended: false,
  fed_funded_ports: false,
  non_fed_funded_ports: false,
  authorized_subrecipients: false,
  num_fed_funded_ports_zero: false,
  num_fed_funded_ports_less_than: false,
  num_fed_funded_ports_greater_than: false,
  num_non_fed_funded_ports_zero: false,
  num_non_fed_funded_ports_less_than: false,
  num_non_fed_funded_ports_greater_than: false,
};

/**
 * StationForm
 * UI Form for submitting station location information (module 1)
 * Available to sub-recipients and direct-recipients
 */
function StationForm() {
  /**
   * Method for changing the location / route
   */
  const navigate = useNavigate();

  /**
   * Get the api url from the environment variables
   */
  const API_URL = import.meta.env.VITE_API_URL;

  /**
   * Get access and id token for endpoint authorization
   */
  const id_token = localStorage.getItem("id_token");
  const access_token = localStorage.getItem("access_token");

  /**
   * Feature flag management
   * Toggles:
   *  * Check for number of ports created in the ui equal to number of ports entered
   *  * Ability for sub-recipients to create stations
   */

  const [isRemovePortsConfirmationModalOpen, setIsRemovePortsConfirmationModalOpen] = useState(false);
  const [SRAddsStationFeatureFlag, setSRAddsStationFeatureFlag] = useState(false);
  const [RegisterNonFedFundedStationFeatureFlag, setRegisterNonFedFundedStationFeatureFlag] = useState(false);
  useEffect(() => {
    getFeatureFlagList().then((results) => {
      setSRAddsStationFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.SRAddsStation));
      setRegisterNonFedFundedStationFeatureFlag(
        getFeatureFlagValue(results, FeatureFlagEnum.RegisterNonFedFundedStation),
      );
    });
  }, []);

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
   * The options returned from the /org/direct-recipients endpoint for use in the combobox
   * for sub recipients selecting the direct funding recipient that is associated with station
   */
  const [directRecipientOptions, setDirectRecipientOptions] = useState<OrganizationSummary[]>([
    {
      org_id: "",
      recipient_type: "",
      name: "",
      org_friendly_id: "",
    },
  ]);

  /**
   * The direct recipient options converted to a list for use within the combobox component
   * Label is a concatenation of the organization name and the friendly id
   */
  const directRecipientsList = directRecipientOptions?.map(
    (item: { org_id: string; name: string; org_friendly_id: string }) => ({
      value: item.org_id,
      label: `${item.name} - ${item.org_friendly_id}`,
    }),
  );

  /**
   * Manage if options have been fetched from API, otherwise render a spinner while options load
   */
  const [renderDRSelectionOptions, setRenderDRSelectionOptions] = useState<boolean>(false);

  /**
   * When data is uploading show spinner
   **/
  const [isUploadingData, setIsUploadingData] = useState<boolean>(false);

  /**
   * The options returned from the network providers endpoint for use in the combobox
   * within station information section
   */
  const [networkProviderOptions, setNetworkProviderOptions] = useState<NetworkProviderInfo[]>([]);

  /**
   * The network provider options converted to a list for use within the combobox component
   */
  const networkProvidersList = networkProviderOptions?.map(
    (item: { network_provider_uuid: string; network_provider_value: string; description: string }) => ({
      value: item.network_provider_value,
      label: item.description,
    }),
  );

  /**
   * The states options converted to a list for use within the combobox component
   */
  const stateList: any = Object.entries(states).map(([key, value]) => ({
    value: key,
    label: value,
  }));

  /**
   * State variables for managing open/closed for modals on page
   */
  const [isCancelModalOpen, setCancelModalOpen] = useState(false);
  const [isSRSubmitModalOpen, setIsSRSubmitModalOpen] = useState(false);

  /**
   * Manage opening / closing cancel modal
   */
  const openModal = () => {
    setCancelModalOpen(true);
  };
  const closeModal = () => {
    setCancelModalOpen(false);
  };

  /**
   * Function to close the remove ports modal called before ports are auto removed
   */
  const closeRemovePortsConfirmationModal = () => {
    setIsRemovePortsConfirmationModalOpen(false);
    const radioButton = document.getElementById("input-yes-radio-funded") as HTMLInputElement;
    if (radioButton) {
      radioButton.click();
    }
  };

  const confirmAndCloseRemovePortsConfirmationModal = () => {
    // const copiedfedFundedPorts = [...fedFundedPorts];
    const newSelectedPorts: PortsInfo[] = [];
    const newFedFundedPorts: number[] = [];
    setFedFundedPorts(newFedFundedPorts);
    setSelectedFedFundedPorts(newSelectedPorts);
    updateField("fed_funded_ports", newSelectedPorts);

    // resetting all funding type options to false
    updateField("num_fed_funded_ports", 0);
    fundingOptionsListLeft.map((option) => updateField(option.name, 0));
    fundingOptionsListRight.map((option) => updateField(option.name, 0));
    setIsRemovePortsConfirmationModalOpen(false);
    setIsStationFederallyFunded(false);
  };

  /**
   * Functions to open remove ports modal called before ports are auto removed
   */
  const openRemovePortsConfirmationModal = () => {
    setIsRemovePortsConfirmationModalOpen(true);
  };

  /**
   * Manage opening/ closing sr adding station confirm modal
   */
  const openSRAddStationModal = () => {
    setIsSRSubmitModalOpen(true);
  };
  const closeSRAddStationModal = () => {
    setIsSRSubmitModalOpen(false);
  };

  /**
   * Is user in edit mode
   * If true, editing station details (with uuid from path)
   * If false, creation of a new station
   */
  const [editMode, setEditMode] = useState<boolean>(false);
  const [stationUuid, setStationUuid] = useState<string>();

  /**
   * Determine if user is in edit mode and get station id if applicable
   */
  useEffect(() => {
    const urlParts = window.location.href.split("/");
    if (urlParts[urlParts.length - 1] === "edit") {
      // station id
      setStationUuid(urlParts[urlParts.length - 2]);
      setEditMode(true);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      setDefaultOperationalDate("not-added");
      setDefaultAFC(-1);
    }
  }, []);

  /**
   * Get recipient type and org information
   */
  const recipientType = getScope();
  const [orgID, setOrgID] = useState("");
  useEffect(() => {
    const jwtOrgID = getOrgID();
    if (jwtOrgID) {
      setOrgID(jwtOrgID);
    }
  }, []);

  /**
   * State variable to keep track of what fields have been updated if in edit form for patch station
   */
  const [editedValues, setEditedValues] = useState<EditedStationValues>({});
  useEffect(() => {
    setEditedValues({ station_uuid: stationUuid });
  }, [stationUuid]);

  /**
   * For use in edit mode, keep track of the original ids for ports and subrecipients associated to the station
   */
  const [originalPorts, setOriginalPorts] = useState<PortsInfo[]>([]);
  const [originalSubrecipients, setOriginalSubrecipients] = useState<string[]>([]);

  /**
   * For use in edit mode, the original/ default selection to render, set by the endpoint
   */
  const [defaultNetworkProvider, setDefaultNetworkProvider] = useState<string>();
  const [defaultOperationalDate, setDefaultOperationalDate] = useState<string>();
  const [defaultAFC, setDefaultAFC] = useState<number>();
  const [defaultFederallyFunded, setDefaultFederallyFunded] = useState<boolean>();

  /**
   * Maintain list of all invalid fields when user attempts to add/update station
   */
  const [invalidField, setInvalidField] = useState<{ [key: string]: boolean }>(initialErrorState);

  /**
   * Maintain list of all missing fields that are requiredwhen user attempts to add/update station
   */
  const [missingRequiredMessage, setMissingRequiredMessage] = useState<{
    [key: string]: boolean;
  }>(initialErrorState);

  /**
   * Maintain list of any custom errors (over characters, not numbers, etc) when user attempts to add/update station
   */
  const [customErrors, setCustomErrors] = useState<{ [key: string]: boolean }>(InitialCustomErrors);

  /**
   * Boolean for if user attempts to create a station with the same id as an existing station
   */
  const [duplicateStationError, setDuplicateStationError] = useState(false);

  /**
   * Boolean for if user attempts to create a station with the same id as an existing station
   */
  const [unableToDeletePortError, setUnableToDeletePortError] = useState(false);

  /**
   * Boolean for if user attempts to create a station with the same id as an existing station
   */
  const [portsWithData, setPortsWithData] = useState<string[]>([]);

  /**
   * Boolean to track if current station is federally funded
   */
  const [isStationFederallyFunded, setIsStationFederallyFunded] = useState<boolean | null>(null);

  /**
   * List of the subrecipient entries that contain errors
   */
  const [errorSubrecipients, setErrorSubrecipients] = useState<number[]>([]);
  /**
   * List of the port entries that contain errors
   */
  const [errorPortsIDs, setErrorPortIDs] = useState<number[]>([]);

  /**
   * State variable for all fields that contain labels for summary banner at top of page
   */
  const [incorrectValues, setIncorrectValues] = useState<string[]>([]);

  /**
   * get direct recipient name from direct recipient list
   * @param dr_id the org id for the recipient
   * @returns the organization name
   */
  const getDRNameById = (dr_id: string) => {
    const org = directRecipientOptions.find((org) => org.org_id === dr_id);
    return org ? org.name : "Unknown";
  };

  /**
   * form state values for API submission
   */
  const [stationValues, setStateValues] = useState<StationAddNew>({
    address: "",
    city: "",
    project_type: "",
    station_id: "",
    latitude: "",
    longitude: "",
    nickname: "",
    federally_funded: null,
    num_fed_funded_ports: null,
    num_non_fed_funded_ports: null,
    state: "undefined",
    status: "Active",
    network_provider: "",
    operational_date: "",
    NEVI: 0,
    CFI: 0,
    EVC_RAA: 0,
    CMAQ: 0,
    CRP: 0,
    OTHER: 0,
    AFC: undefined,
    authorized_subrecipients: [],
    zip: "",
    zip_extended: "",
    fed_funded_ports: [],
    non_fed_funded_ports: [],
    dr_id: getOrgID(), //passing in dr_id needed for sr adds station
  });

  /**
   * Get lists of organizations
   * If user is a direct recipient, get sub recipients for step 2 (Authorize Contractors)
   * Else if user is a sub recipient, get direct recipients for step 1 (Select Direct Funding Recipient for Station)
   */
  useEffect(() => {
    if (recipientType === "direct-recipient") {
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
    } else if (recipientType === "sub-recipient") {
      // passing in the route so that we can get back the entire list of DRs instead of just the authorized list
      const queryParams = `route=station_registration`;
      fetch(`${API_URL}${PATH_DIRECT_RECIPIENTS}?${queryParams}`, {
        method: "GET",
        headers: {
          Authorization: `${id_token}`,
          route: "station_registration",
        },
      })
        .then((response) => response.json())
        .then((data) => {
          setDirectRecipientOptions(data);
        })
        .catch((err) => {
          console.log(err.message);
        })
        .finally(() => setRenderDRSelectionOptions(true));
    }
  }, []);

  /**
   * Get network providers for station location information combobox
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
        setNetworkProviderOptions(data);
      })
      .catch((err) => {
        console.log(err.message);
      });
  }, []);

  /**
   * If in edit mode, get data and set all fields in form to match current station information
   */
  useEffect(() => {
    if (orgID && editMode) {
      fetch(`${API_URL}${PATH_STATION_ID}?station_uuid=${stationUuid}`, {
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
          if (data.authorized_subrecipients && data.authorized_subrecipients !== "") {
            updateSRMapping(data.authorized_subrecipients);
          }
          if (data.fed_funded_ports.length > 0) {
            updateFedFundedPortsMapping(data.fed_funded_ports);
          }
          if (data.non_fed_funded_ports.length > 0) {
            updateNonFedFundedPortsMapping(data.non_fed_funded_ports);
          }
          if (
            data.operational_date !== null &&
            /^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$/.test(data.operational_date)
          ) {
            setDefaultOperationalDate(data.operational_date);
          } else {
            setDefaultOperationalDate("not-added");
          }
          setDefaultNetworkProvider(data.network_provider);
          setDefaultAFC(data.AFC);
          setOriginalPorts(data.fed_funded_ports.concat(data.non_fed_funded_ports));

          const hasFedStationsRegistered = Boolean(data.num_fed_funded_ports >= 1);
          setDefaultFederallyFunded(hasFedStationsRegistered);
          setIsStationFederallyFunded(hasFedStationsRegistered);
        })
        .catch((err) => {
          console.log(err.message);
          const errorCode = err.status;

          if (errorCode === 403) {
            navigate(ROUTE_NOT_AUTHORIZED);
          }
        });
    }
  }, [orgID, subrecipientOptions, networkProviderOptions]);

  /**
   * Function used when station is in edit mode to populate the comboboxes in section two
   * with the previously authorized subrecipients so the user can add/remove/edit
   * @param sr_object array containing an object with the subrecipients name and org_id
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
   * If in edit mode, get the "default" value for the combobox based on the id
   * @param index which subrecipient should be populated in the combobox
   * @returns the org_id of the subrecipient
   */
  function getSubRecipientComboboxDefaultValue(index: number) {
    return stationValues.authorized_subrecipients[index];
  }

  /**
   * Function used when station is in edit mode to populate the port id / port type sections
   * @param ports_object the returned port information from the endpoint containing the previously provided
   * station ports
   */
  function updateFedFundedPortsMapping(ports_object: PortsInfo[]) {
    const comboBoxIds = Array.from({ length: Object.keys(ports_object).length }, () =>
      Number(Math.floor(Math.random() * 100_000_000)),
    );
    setFedFundedPorts(comboBoxIds);
    setSelectedFedFundedPorts(ports_object);
    updateField("fed_funded_ports", ports_object);
  }

  /**
   * Function used when station is in edit mode to populate the port id / port type sections
   * @param ports_object the returned port information from the endpoint containing the previously provided
   * station ports
   */
  function updateNonFedFundedPortsMapping(ports_object: PortsInfo[]) {
    const comboBoxIds = Array.from({ length: Object.keys(ports_object).length }, () =>
      Number(Math.floor(Math.random() * 100_000_000)),
    );
    setNonFedFundedPorts(comboBoxIds);
    setSelectedNonFedFundedPorts(ports_object);
    updateField("non_fed_funded_ports", ports_object);
  }

  /**
   * Function used when station is in edit mode to populate port type
   * @param index the index to be retrieved
   * @param funding the funding type (fed_funded / non_fed_funded)
   * @returns the port type
   */
  function getPortTypeDefaultValue(index: number, funding: string) {
    if (funding === "fed_funded" && index < stationValues.fed_funded_ports.length) {
      return stationValues.fed_funded_ports[index].port_type;
    } else if (funding === "non_fed_funded" && index < stationValues.non_fed_funded_ports.length) {
      return stationValues.non_fed_funded_ports[index].port_type;
    } else {
      return "";
    }
  }

  /**
   * Function used when station is in edit mode to populate port id
   * @param index the index to be retrieved
   * @param funding the funding type (fed_funded / non_fed_funded)
   * @returns the port id
   */
  function getPortTextInputDefaultValue(index: number, funding: string) {
    if (funding === "fed_funded" && index < stationValues.fed_funded_ports.length) {
      return stationValues.fed_funded_ports[index].port_id;
    } else if (funding === "non_fed_funded" && index < stationValues.non_fed_funded_ports.length) {
      return stationValues.non_fed_funded_ports[index].port_id;
    } else {
      return "";
    }
  }

  /**
   * Function used when station is in edit mode to get the number of port
   * @param type the funding type (fed_funded / non_fed_funded)
   * @returns the number of ports previously provided
   */
  const getDefaultNumPorts = (type: string): string | undefined => {
    if (type === "fed" && stationValues.num_fed_funded_ports !== null) {
      return String(stationValues.num_fed_funded_ports);
    } else if (type === "non_fed" && stationValues.num_non_fed_funded_ports !== null) {
      return String(stationValues.num_non_fed_funded_ports);
    } else {
      return undefined;
    }
  };

  /**
   * Function tied to updating fields throughout the form
   * @param fieldName the name of the field being updated
   * @param value the associated value
   */
  const updateField = (fieldName: string, value: any): any => {
    setStateValues((prevState) => ({
      ...prevState,
      [fieldName]: value,
    }));

    setInvalidField((prevValidity) => ({
      ...prevValidity,
      [fieldName]: false,
    }));

    setMissingRequiredMessage((prevValidity) => ({
      ...prevValidity,
      [fieldName]: false,
    }));

    setCustomErrors((prevValidity) => ({
      ...prevValidity,
      [fieldName]: false,
    }));

    if (Object.prototype.hasOwnProperty.call(characterLimits, fieldName)) {
      if (value != null && value.length > characterLimits[fieldName]) {
        setInvalidField((prevValidity) => ({
          ...prevValidity,
          [fieldName]: true,
        }));
      }
    }

    if (editMode) {
      setEditedValues((prevState) => ({
        ...prevState,
        [fieldName]: value,
      }));
    }
  };

  /**
   * Event tied to date picker component
   * Sets the correctly formatted operational date in the state form
   * @param date the passed date object from the date picker
   */
  const updateOperationalDate = (date: string | undefined) => {
    if (date !== undefined) {
      const formattedDate = convertDateFormat(date);
      updateField("operational_date", formattedDate);
    }
  };

  /**
   * Event tied to selecting/ updating station on afc in station profile
   * @param value the value for if station is afc (0 yes, 1 no)
   */
  const updateAFCField = (value: string) => {
    updateField("AFC", Number(value));
  };

  /**
   * Event tied to selecting/ updating state in station profile
   * @param e the event containing the selected state
   */
  const updateStateChoice = (e: SyntheticEvent<HTMLInputElement>) => {
    updateField("state", (e.target as HTMLInputElement).value);
  };

  /**
   * Event tied to selecting/ updating network provider in station profile
   * @param value the selected network provider
   */
  const handleNetworkProviderChange = (value: string) => {
    updateField("network_provider", value);
  };

  /**
   * Function to checkboxes for selecting funding type
   * @param field the funding type (NEVI, CFI, EVC_RAA, CMAQ, CRP, OTHER)
   */
  const handleFundingTypeChange = (field: keyof StationAddNew) => {
    const newValue = stationValues[field] === 0 ? 1 : 0;
    updateField(field, newValue);
    setMissingRequiredMessage((prevValidity) => ({
      ...prevValidity,
      funding_type: false,
    }));
    setInvalidField((prevValidity) => ({
      ...prevValidity,
      funding_type: false,
    }));
  };

  /**
   * Available funding types and their descriptions
   */
  const fundingOptionsListLeft = [
    { name: "NEVI", description: "National Electric Vehicle Infrastructure" },
    {
      name: "EVC_RAA",
      description: "Electric Vehicle Charger Reliability and Accessibility Accelerator",
    },
    {
      name: "CFI",
      description: "Charging and Fueling Infrastructure Discretionary Grant Program",
    },
  ];
  const fundingOptionsListRight = [
    { name: "CRP", description: "Carbon Reduction Program" },
    { name: "CMAQ", description: "Congestion Mitigation and Air Quality" },
    { name: "OTHER", description: "Funding program is not listed" },
  ];

  /**
   * State variable to uniquely identify each subrecipient combobox created through the UI
   */
  const [authorizeSubrecipients, setAuthorizeSubrecipients] = useState<number[]>([]);
  /**
   * State variable to keep track of the subrecipients a user has selected
   */
  const [selectedSubrecipients, setSelectedSubrecipients] = useState<string[]>([]);

  /**
   * State variable to uniquely identify each federal port addition section (id/type) created through the UI
   */
  const [fedFundedPorts, setFedFundedPorts] = useState<number[]>([]);
  /**
   * State variable to keep track of the information for federal ports a user has entered
   */
  const [selectedFedFundedPorts, setSelectedFedFundedPorts] = useState<PortsInfo[]>([]);

  /**
   * State variable to uniquely identify each non federal port addition section (id/type) created through the UI
   */
  const [nonFedFundedPorts, setNonFedFundedPorts] = useState<number[]>([]);
  /**
   * State variable to keep track of the information for non federal ports a user has entered
   */
  const [selectedNonFedFundedPorts, setSelectedNonFedFundedPorts] = useState<PortsInfo[]>([]);

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
   * Event tied to "Station Uses Federal Funds" on Station Profile section
   * Updates the isFederallyFunded boolean based on user input, if station is not federally funded,
   * the funding type options are cleared out
   */
  const handleIsStationFederallyFunded = (value: string) => {
    // if station is not federally funded, all non-federal port info should be required, while all federal info should not be
    // No
    setIsStationFederallyFunded(Boolean(Number(value)));
    updateField("federally_funded", value);

    if (value === "0") {
      // If fed funded ports exist trigger confirmation modal
      if (fedFundedPorts.length > 0 || stationValues.fed_funded_ports.length > 0) {
        openRemovePortsConfirmationModal();
        // if confirmed call confirmAndCloseRemovePortsConfirmationModal
      } else {
        // resetting all funding type options to false
        fundingOptionsListLeft.map((option) => updateField(option.name, 0));
        fundingOptionsListRight.map((option) => updateField(option.name, 0));

        // reset all values for federal funded ports
        updateField("num_fed_funded_ports", 0);
      }

      // if station is federally funded, all non-federal port info should be non-required
      // Yes
    } else if (value === "1") {
      // reset all error checks for non-federal funded ports to be non requried
      updateField("num_non_fed_funded_ports", stationValues.num_non_fed_funded_ports);
      updateField("non_fed_funded_ports", stationValues.non_fed_funded_ports);
      customErrors.num_non_fed_funded_ports_zero = false;
      missingRequiredMessage.num_non_fed_funded_ports = false;
    }
  };

  /**
   * Event tied to "Add Port" on Federally Funded Port IDs section
   * Creates a new empty section (id field and port type drop down) for the user to enter information
   */
  const handleAddFedFundedPortChange = () => {
    const newPortId = Math.floor(Math.random() * 100_000_000);
    setFedFundedPorts([...fedFundedPorts, newPortId]);
    setSelectedFedFundedPorts([
      ...selectedFedFundedPorts,
      {
        port_id: "",
        port_type: "",
      },
    ]);
  };

  /**
   * Event tied to "Add Port" on Non-Federally Funded Port IDs section
   * Creates a new empty section (id field and port type drop down) for the user to enter information
   */
  const handleAddNonFedFundedPortChange = () => {
    const newPortId = Math.floor(Math.random() * 100_000_000);
    setNonFedFundedPorts([...nonFedFundedPorts, newPortId]);
    setSelectedNonFedFundedPorts([
      ...selectedNonFedFundedPorts,
      {
        port_id: "",
        port_type: "",
      },
    ]);
  };

  /**
   * Event tied to "Remove" on Federally Funded Port IDs section
   * Removes the section entirely from the UI and the previously entered information
   */
  const handleRemoveFedFundedPort = (portComboboxID: number) => {
    setFedFundedPorts(fedFundedPorts.filter((id) => id !== portComboboxID));
    const newSelectedValues = [...selectedFedFundedPorts];
    const indexToRemove = fedFundedPorts.indexOf(portComboboxID);
    if (indexToRemove !== -1) {
      newSelectedValues.splice(indexToRemove, 1);
      setSelectedFedFundedPorts(newSelectedValues);
      updateField("fed_funded_ports", newSelectedValues);
    } else {
      console.log("couldn't find indexToRemove: ", fedFundedPorts.indexOf(portComboboxID));
    }
    setErrorPortIDs(errorPortsIDs.filter((id) => id !== portComboboxID));
  };

  /**
   * Event tied to "Remove" on Non-Federally Funded Port IDs section
   * Removes the section entirely from the UI and the previously entered information
   */
  const handleRemoveNonFedFundedPort = (portComboboxID: number) => {
    setNonFedFundedPorts(nonFedFundedPorts.filter((id) => id !== portComboboxID));
    const newSelectedValues = [...selectedNonFedFundedPorts];
    const indexToRemove = nonFedFundedPorts.indexOf(portComboboxID);
    if (indexToRemove !== -1) {
      newSelectedValues.splice(indexToRemove, 1);
      setSelectedNonFedFundedPorts(newSelectedValues);
      updateField("non_fed_funded_ports", newSelectedValues);
    }
    setErrorPortIDs(errorPortsIDs.filter((id) => id !== portComboboxID));
  };

  /**
   * Event tied to user updating the port id field in Federally Funded Port IDs section
   * @param value the user provided id
   * @param index the index of the field being updated
   * @param portComboboxID the id for the field being changed
   */
  const handleFedFundedPortChange = (value: any, index: number, portComboboxID: number) => {
    const newSelectedPorts = [...selectedFedFundedPorts];
    newSelectedPorts[index].port_id = value;
    setSelectedFedFundedPorts(newSelectedPorts);
    updateField("fed_funded_ports", newSelectedPorts);
    setErrorPortIDs(errorPortsIDs.filter((id) => id !== portComboboxID));

    if (value.length > characterLimits["port_id"]) {
      setErrorPortIDs([...errorPortsIDs, portComboboxID]);
    }
  };

  /**
   * Event tied to user updating the port id field in Non-Federally Funded Port IDs section
   * @param value the user provided id
   * @param index the index of the field being updated
   * @param portComboboxID the id for the field being changed
   */
  const handleNonFedFundedPortChange = (value: any, index: number, portComboboxID: number) => {
    const newSelectedPorts = [...selectedNonFedFundedPorts];
    newSelectedPorts[index].port_id = value;
    setSelectedNonFedFundedPorts(newSelectedPorts);
    updateField("non_fed_funded_ports", newSelectedPorts);
    setErrorPortIDs(errorPortsIDs.filter((id) => id !== portComboboxID));

    if (value.length > characterLimits["port_id"]) {
      setErrorPortIDs([...errorPortsIDs, portComboboxID]);
    }
  };

  /**
   * Event tied to user updating the port type field in Federally Funded Port IDs section
   * @param value the value (L2/DCFC) that was selected
   * @param index the index of the field being updated
   */
  const handleFedPortTypeChange = (value: any, index: number) => {
    const newSelectedPorts = [...selectedFedFundedPorts];
    newSelectedPorts[index].port_type = value;
    setSelectedFedFundedPorts(newSelectedPorts);
    updateField("fed_funded_ports", newSelectedPorts);
  };

  /**
   * Event tied to user updating the port type field in Non-Federally Funded Port IDs section
   * @param value the value (L2/DCFC) that was selected
   * @param index the index of the field being updated
   */
  const handleNonFedPortTypeChange = (value: any, index: number) => {
    const newSelectedPorts = [...selectedNonFedFundedPorts];
    newSelectedPorts[index].port_type = value;
    setSelectedNonFedFundedPorts(newSelectedPorts);
    updateField("non_fed_funded_ports", newSelectedPorts);
  };

  /**
   * Check if subrecipient / ports contain errors, and return appropriate class name to highlight field
   * @param type the type of field being checked
   * @param num the id of the component to check
   * @returns the class name
   */
  const checkEntriesError = (type: string, num: number) => {
    if (type === "subrecipient") {
      if (errorSubrecipients.includes(num)) {
        return "error-combobox";
      } else {
        return "";
      }
    } else if (type === "port") {
      if (errorPortsIDs.includes(num)) {
        return "usa-input--error";
      } else {
        return "";
      }
    }
  };

  /**
   * Get all parameters needed for checkValidData
   * @returns a list of the parameters needed to be passed into checkValidData
   */
  const getParametersForCheckValidData = (): [
    StationAddNew,
    { [key: string]: boolean },
    { [key: string]: boolean },
    { [key: string]: boolean },
    { [key: string]: boolean },
    boolean,
    string[],
    number[],
    PortsInfo[],
    PortsInfo[],
    number[],
    number[],
    boolean | null,
    React.Dispatch<React.SetStateAction<string[]>>,
    React.Dispatch<React.SetStateAction<number[]>>,
    React.Dispatch<React.SetStateAction<number[]>>,
    React.Dispatch<React.SetStateAction<{ [key: string]: boolean }>>,
    React.Dispatch<React.SetStateAction<{ [key: string]: boolean }>>,
    React.Dispatch<React.SetStateAction<{ [key: string]: boolean }>>,
  ] => {
    return [
      stationValues,
      customErrors,
      invalidField,
      missingRequiredMessage,
      { SRAddsStationFeatureFlag, RegisterNonFedFundedStationFeatureFlag },
      duplicateStationError,
      selectedSubrecipients,
      authorizeSubrecipients,
      selectedFedFundedPorts,
      selectedNonFedFundedPorts,
      fedFundedPorts,
      nonFedFundedPorts,
      isStationFederallyFunded,
      setIncorrectValues,
      setErrorSubrecipients,
      setErrorPortIDs,
      setInvalidField,
      setMissingRequiredMessage,
      setCustomErrors,
    ];
  };

  /**
   * Handle subrecipient adding a station
   */
  const handleSRAddStation = () => {
    updateField("status", "Pending Approval");
    updateField("authorized_subrecipients", [getOrgID()]);

    if (checkValidData(...getParametersForCheckValidData())) {
      openSRAddStationModal();
    } else {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  /**
   * Function to render on station creation success the newly authorized sub recipients
   * @returns the full list of subrecipients with their org names
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
   * Function to handle saving/ updating a station
   */
  const handleSaveStation = async () => {
    const updatedinvalidField = { ...invalidField };
    if (checkValidData(...getParametersForCheckValidData())) {
      // If the data is valid, start prepping for submit
      const submitEditedData = { ...editedValues };

      if (stationValues.status === "Pending Approval") {
        submitEditedData.status = "Active";
      }

      if (defaultNetworkProvider?.trim() === stationValues.network_provider.trim()) {
        delete submitEditedData.network_provider;
      }

      if (
        submitEditedData.hasOwnProperty("num_non_fed_funded_ports") &&
        String(submitEditedData.num_non_fed_funded_ports) === ""
      ) {
        submitEditedData.num_non_fed_funded_ports = null;
      }

      if (submitEditedData.hasOwnProperty("network_provider")) {
        submitEditedData.station_id = stationValues.station_id;
      }

      if (submitEditedData.hasOwnProperty("station_id")) {
        submitEditedData.network_provider = stationValues.network_provider;
      }

      // SR Added
      const srs_added = selectedSubrecipients.filter((uuid) => !originalSubrecipients.includes(uuid));
      if (srs_added.length !== 0) {
        submitEditedData.srs_added = srs_added;
      }

      // SR Removed
      const srs_removed = originalSubrecipients.filter((uuid) => !selectedSubrecipients.includes(uuid));
      if (srs_removed.length !== 0) {
        submitEditedData.srs_removed = srs_removed;
      }

      // Ports Removed
      const all_ports_removed = originalPorts
        .filter(
          (port_uuid) => !selectedFedFundedPorts.includes(port_uuid) && !selectedNonFedFundedPorts.includes(port_uuid),
        )
        .map((port) => port.port_uuid!);
      if (all_ports_removed.length !== 0) {
        submitEditedData.ports_removed = all_ports_removed;
      }

      // Remove authorized subrecipients field
      if (editedValues.authorized_subrecipients) {
        delete submitEditedData.authorized_subrecipients;
      }

      const submitData = { ...submitEditedData, federally_funded: isStationFederallyFunded };
      setIsUploadingData(true);
      fetch(`${API_URL}${PATH_STATIONS}`, {
        method: "PATCH",
        headers: {
          Authorization: `${access_token}`,
        },
        body: JSON.stringify(submitData),
      })
        .then((response) => {
          if (response.ok) {
            {
              // eslint-disable-next-line @typescript-eslint/no-unused-expressions
              Object.prototype.hasOwnProperty.call(submitEditedData, "status")
                ? navigate(ROUTE_STATIONS, {
                    state: {
                      createSuccess: true,
                      authorizedSrNamesList: getAuthorizedSrNamesByOrgId(),
                      drName: getOrgName(),
                    },
                  })
                : navigate(ROUTE_STATIONS, {
                    state: { updateSuccess: true },
                  });
            }
          } else {
            throw response;
          }
        })
        .catch(async (err) => {
          const errorCode = err.status;
          const errorMsg = await extract_error_body(err);
          if (errorCode === 409) {
            if (errorMsg.includes("EvChartUnableToDeleteItemError")) {
              setUnableToDeletePortError(true);
              const error_parts = errorMsg.split(":");
              if (error_parts.length === 2) {
                const commaDelimitedString = error_parts[1];
                const formattedString = commaDelimitedString.replace(/['"]+/g, "");
                const values = formattedString.split(",");
                setPortsWithData(values);
              }
              console.log(errorMsg);
            } else {
              setDuplicateStationError(true);
              updatedinvalidField.station_id = true;
              updatedinvalidField.network_provider = true;
              setIncorrectValues((prevArray) => [...prevArray, "Station ID", "Network Provider"]);
              setInvalidField(updatedinvalidField);
            }
            window.scrollTo({ top: 0, behavior: "smooth" });
          }
        })
        .finally(() => {
          setIsUploadingData(false);
        });
    } else {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  async function extract_error_body(err: unknown): Promise<string> {
    if (err instanceof Response) {
      try {
        return await err.text();
      } catch {
        if (err.body) {
          return await readable_stream_to_string(err.body);
        }
      }
    }

    if (err instanceof Error) {
      return err.message;
    }
    return JSON.stringify(err);
  }

  async function readable_stream_to_string(err_stream: ReadableStream<Uint8Array>): Promise<string> {
    const reader = err_stream.getReader();
    const decoder = new TextDecoder("utf-8");
    let result = "";

    // eslint-disable-next-line no-constant-condition
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      result += decoder.decode(value, { stream: true });
    }

    result += decoder.decode();
    return result;
  }

  /**
   * Function to handle creating a new station
   */
  const handleAddStation = async () => {
    if (checkValidData(...getParametersForCheckValidData())) {
      setIsUploadingData(true);
      const updatedinvalidField = { ...invalidField };
      const submitData = { ...stationValues, federally_funded: isStationFederallyFunded };
      fetch(`${API_URL}${PATH_STATIONS}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `${access_token}`,
        },
        body: JSON.stringify(submitData),
      })
        .then((response) => {
          if (response.ok) {
            navigate(ROUTE_STATIONS, {
              state: {
                createSuccess: true,
                authorizedSrNamesList: getAuthorizedSrNamesByOrgId(),
                drName: isDRUser() ? getOrgName() : getDRNameById(stationValues.dr_id),
              },
            });
          } else {
            throw response;
          }
        })
        .catch((err) => {
          const errorCode = err.status;
          if (errorCode === 409) {
            setDuplicateStationError(true);
            updatedinvalidField.station_id = true;
            updatedinvalidField.network_provider = true;
            setIncorrectValues((prevArray) => [...prevArray, "Station ID", "Network Provider"]);
            setInvalidField(updatedinvalidField);
            closeSRAddStationModal();
            window.scrollTo({ top: 0, behavior: "smooth" });
          }
        })
        .finally(() => {
          setIsUploadingData(false);
        });
    } else {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  /**
   * Breadcrumb bar for page
   * @returns the breadcrumb bar
   */
  const DefaultBreadcrumb = (): React.ReactElement => (
    <BreadcrumbBar>
      <Breadcrumb>
        <BreadcrumbLink href={ROUTE_HOME}>
          <span>Home</span>
        </BreadcrumbLink>
      </Breadcrumb>
      <Breadcrumb>
        <BreadcrumbLink href={ROUTE_STATIONS}>
          <span>Stations</span>
        </BreadcrumbLink>
      </Breadcrumb>
      <Breadcrumb current>{editMode ? <span>Edit Station</span> : <span>Add Station</span>}</Breadcrumb>
    </BreadcrumbBar>
  );

  /**
   * Funding type checkbox section
   * @returns different funding type checkbox options
   */
  function FundingTypeOptions() {
    return (
      <div>
        <Grid row gap>
          <Grid col={7} className="form-field">
            <FormLabelAndTooltip
              formLabel="Funding Type"
              tooltipLabel={`Federal funding program(s) directing funds to a project associated with a station.`}
              htmlFor="input-FundingType"
              requiredField={true}
            />

            {missingRequiredMessage.funding_type && <ErrorMessage>This field is required</ErrorMessage>}
          </Grid>
        </Grid>

        <Grid row gap>
          <Grid col={2} className="form-field funding-type-options">
            {fundingOptionsListLeft.map((option) => (
              <Checkbox
                id={`fundingTypeOption${option.name}`}
                name="checkbox"
                key={`fundingTypeOption${option.name}`}
                label={
                  <div className="label-tooltip-container">
                    {option.name.replace("_", "-")}
                    <Tooltip label={option.description} asCustom={CustomLink}>
                      <Icon.InfoOutline className="tooltip-icon" />
                    </Tooltip>
                  </div>
                }
                checked={stationValues[option.name as keyof StationAddNew] === 1}
                onChange={() => handleFundingTypeChange(option.name.toUpperCase() as keyof StationAddNew)}
              />
            ))}
          </Grid>
          <Grid col={5} className="form-field funding-type-options">
            {fundingOptionsListRight.map((option) => (
              <Checkbox
                id={`fundingTypeOption${option.name}`}
                name="checkbox"
                key={`fundingTypeOption${option.name}`}
                label={
                  <div className="label-tooltip-container">
                    {option.name === "OTHER" ? "Other Federal Funding - Not Listed" : option.name}
                    <Tooltip label={option.description} asCustom={CustomLink}>
                      <Icon.InfoOutline className="tooltip-icon" />
                    </Tooltip>
                  </div>
                }
                checked={stationValues[option.name as keyof StationAddNew] === 1}
                onChange={() => handleFundingTypeChange(option.name.toUpperCase() as keyof StationAddNew)}
              />
            ))}
          </Grid>
        </Grid>
      </div>
    );
  }

  /**
   * Port information section
   * @returns input fields for number of ports and addition of port ids
   */
  function PortInformation() {
    return (
      <div>
        <Grid col={8}>
          <h2 className="station-form-header">
            {" "}
            {`Step ${!RegisterNonFedFundedStationFeatureFlag ? "3" : "4"}: Port Information`}{" "}
          </h2>
          <p>
            A charging port is the system within a charger that charges one EV. A charging port may have multiple
            connectors, but it can provide power to only one EV through one connector at a time. In cases where more
            than one charging port on a charger exists, each charging port must be uniquely identified by a charging
            port ID.
          </p>
        </Grid>
        {(isStationFederallyFunded === true ||
          isStationFederallyFunded === null ||
          RegisterNonFedFundedStationFeatureFlag === false) && (
          <Grid row gap>
            <Grid col={5} className="form-field">
              <div className="label-tooltip-container fixed-width-tooltip">
                <Label htmlFor="num_fed_funded_ports" className="required-field">
                  Number of Federally Funded Ports
                </Label>
              </div>
              <CharacterCount
                id="num_fed_funded_ports"
                name="num_fed_funded_ports"
                type="number"
                maxLength={characterLimits["num_fed_funded_ports"]}
                value={getDefaultNumPorts("fed")}
                className={inputValid(invalidField.num_fed_funded_ports, "field")}
                onChange={(e: ChangeEvent<HTMLInputElement>) => updateField("num_fed_funded_ports", e.target.value)}
                // This is cursed.  Preserving the focus while scrolling the mousewheel and "undoing"
                // the value change based on the direction the wheel was scrolled.  e.preventDefault()
                // cannot be used due to onWheel being a passive event listener (and would break
                // scrolling regardless).
                onWheel={(e: any) => {
                  let value = parseInt(e.target.value);
                  if (isNaN(value) && document.activeElement === e.target) value = 0;

                  e.target.value = `${value + Math.sign(e.deltaY)}`;
                }}
              />
              {missingRequiredMessage.num_fed_funded_ports && !customErrors.num_fed_funded_ports && (
                <ErrorMessage>This field is required</ErrorMessage>
              )}
              {customErrors.num_fed_funded_ports && (
                <ErrorMessage>Use a number with a maximum of 3 digits</ErrorMessage>
              )}
              <ErrorMessage>
                {customErrors.num_fed_funded_ports_zero
                  ? "Number of federally-funded ports must be greater than zero"
                  : customErrors.num_fed_funded_ports_greater_than
                    ? "Number of federally-funded ports is greater than number of Port IDs input"
                    : customErrors.num_fed_funded_ports_less_than
                      ? "Number of federally-funded ports is less than number of Port IDs input"
                      : null}
              </ErrorMessage>
            </Grid>
          </Grid>
        )}

        <Grid row gap>
          <Grid col={5} className="form-field">
            <div className="label-tooltip-container fixed-width-tooltip">
              <Label
                htmlFor="num_non_fed_funded_ports"
                className={
                  RegisterNonFedFundedStationFeatureFlag &&
                  (isStationFederallyFunded === false || defaultFederallyFunded === false)
                    ? "required-field"
                    : ""
                }
              >
                Number of Non-Federally Funded Ports
              </Label>
            </div>
            <CharacterCount
              id="num_non_fed_funded_ports"
              name="num_non_fed_funded_ports"
              type="number"
              maxLength={characterLimits["num_non_fed_funded_ports"]}
              value={getDefaultNumPorts("non_fed")}
              className={inputValid(invalidField.num_non_fed_funded_ports, "field")}
              onChange={(e: any) => updateField("num_non_fed_funded_ports", e.target.value)}
              // This is cursed.  Preserving the focus while scrolling the mousewheel and "undoing"
              // the value change based on the direction the wheel was scrolled.  e.preventDefault()
              // cannot be used due to onWheel being a passive event listener (and would break
              // scrolling regardless).
              onWheel={(e: any) => {
                let value = parseInt(e.target.value);
                if (isNaN(value) && document.activeElement === e.target) value = 0;

                e.target.value = `${value + Math.sign(e.deltaY)}`;
              }}
            />
            {RegisterNonFedFundedStationFeatureFlag &&
              !isStationFederallyFunded &&
              missingRequiredMessage.num_non_fed_funded_ports &&
              !customErrors.num_non_fed_funded_ports && <ErrorMessage>This field is required</ErrorMessage>}

            {customErrors.num_non_fed_funded_ports && (
              <ErrorMessage>Use a number with a maximum of 3 digits</ErrorMessage>
            )}

            <ErrorMessage>
              {customErrors.num_non_fed_funded_ports_zero
                ? "Number of non-federally-funded ports must be greater than zero"
                : customErrors.num_non_fed_funded_ports_greater_than
                  ? "Number of non-federally funded ports is greater than number of Port IDs input"
                  : customErrors.num_non_fed_funded_ports_less_than
                    ? "Number of non-federally funded ports is less than number of Port IDs input"
                    : null}
            </ErrorMessage>
          </Grid>
        </Grid>

        {(isStationFederallyFunded === true ||
          isStationFederallyFunded === null ||
          RegisterNonFedFundedStationFeatureFlag === false) && (
          <Grid row gap>
            <Grid col={8}>
              <h3> Federally Funded Port IDs </h3>
              <p>
                Providing the unique port IDs associated with this charging station allows EV-ChART to accurately track
                historical data at the port level providing greater insights for time series analysis and performance
                management.
              </p>
            </Grid>
          </Grid>
        )}

        {missingRequiredMessage.fed_funded_ports && (
          <Grid row col={8} style={{ marginTop: 15 }}>
            <ErrorMessage>Please enter a unique Port ID for each entry or remove the field.</ErrorMessage>
          </Grid>
        )}

        {(isStationFederallyFunded === true ||
          isStationFederallyFunded === null ||
          RegisterNonFedFundedStationFeatureFlag === false) && (
          <Grid>
            {fedFundedPorts.map((portComboboxID, index) => (
              <Grid className="subrecipient-combobox" key={portComboboxID}>
                <Grid row gap>
                  <Grid col={4}>
                    <FormLabelAndTooltip
                      formLabel="Port ID"
                      tooltipLabel="This uniquely identifies a port. This should be created by the Network Provider and per 23 CFR 680.112, this must be the same value used to identify the charging port in data made available to third parties in 23 CFR 680.116(c)(8)(ii)."
                      htmlFor={`port_id_${portComboboxID}`}
                      requiredField={true}
                    />
                    <CharacterCount
                      id={`input-portComboboxID${portComboboxID}`}
                      name={`input-portComboboxID${portComboboxID}`}
                      type="text"
                      maxLength={characterLimits["port_id"]}
                      className={checkEntriesError("port", portComboboxID)}
                      defaultValue={getPortTextInputDefaultValue(index, "fed_funded")}
                      onChange={(event: any) => handleFedFundedPortChange(event.target.value, index, portComboboxID)}
                    />
                  </Grid>

                  <Grid col={3}>
                    <FormLabelAndTooltip
                      formLabel="Port Type"
                      tooltipLabel="Classification of the port determined by the power they can provide. L2: Level 2 AC charging uses a 208/240 volt AC electric circuit. DCFC: Direct-current fast charger, sometimes referred to as a Level 3 DC charging, uses a 3-phase 480 volt AC electric circuit but delivers direct current (DC) to the vehicle."
                      htmlFor={`port_type_${portComboboxID}`}
                      requiredField={false}
                    />
                    <Select
                      id="port-select"
                      name="port-select"
                      defaultValue={getPortTypeDefaultValue(index, "fed_funded")}
                      onChange={(e) => handleFedPortTypeChange(e.target.value, index)}
                    >
                      <option value=""> - Select - </option>
                      <option value="L2">L2</option>
                      <option value="DCFC">DCFC</option>
                    </Select>
                  </Grid>
                  <Grid>
                    <Button
                      type="button"
                      id={`remove-port-button-${portComboboxID}`}
                      unstyled
                      className="remove-button padding-105 text-center"
                      onClick={() => handleRemoveFedFundedPort(portComboboxID)}
                    >
                      Remove
                    </Button>
                  </Grid>
                </Grid>
              </Grid>
            ))}
            <Button outline className="form-add-button" type="button" onClick={handleAddFedFundedPortChange}>
              Add Port
            </Button>
          </Grid>
        )}

        <Grid row gap>
          <Grid col={8}>
            <h3> Non-Federally Funded Port IDs </h3>
            <p>
              Providing the unique port IDs associated with this charging station allows EV-ChART to accurately track
              historical data at the port level providing greater insights for time series analysis and performance
              management.
            </p>
          </Grid>
        </Grid>

        {missingRequiredMessage.non_fed_funded_ports && (
          <Grid row col={8} style={{ marginTop: 15 }}>
            <ErrorMessage>Please enter a unique Port ID for each entry or remove the field.</ErrorMessage>
          </Grid>
        )}

        <Grid>
          {nonFedFundedPorts.map((portComboboxID, index) => (
            <Grid className="subrecipient-combobox" key={portComboboxID}>
              <Grid row gap>
                <Grid col={4}>
                  <FormLabelAndTooltip
                    formLabel="Port ID"
                    tooltipLabel="This uniquely identifies a port. This should be created by the Network Provider and per 23 CFR 680.112, this must be the same value used to identify the charging port in data made available to third parties in 23 CFR 680.116(c)(8)(ii)."
                    htmlFor={`port_id_${portComboboxID}`}
                    requiredField={true}
                  />
                  <CharacterCount
                    id={`input-portComboboxID${portComboboxID}`}
                    name={`input-portComboboxID${portComboboxID}`}
                    type="text"
                    maxLength={characterLimits["port_id"]}
                    className={checkEntriesError("port", portComboboxID)}
                    defaultValue={getPortTextInputDefaultValue(index, "non_fed_funded")}
                    onChange={(event: any) => handleNonFedFundedPortChange(event.target.value, index, portComboboxID)}
                  />
                </Grid>
                <Grid col={3}>
                  <FormLabelAndTooltip
                    formLabel="Port Type"
                    tooltipLabel="Classification of the port determined by the power they can provide. L2: Level 2 AC charging uses a 208/240 volt AC electric circuit. DCFC: Direct-current fast charger, sometimes referred to as a Level 3 DC charging, uses a 3-phase 480 volt AC electric circuit but delivers direct current (DC) to the vehicle."
                    htmlFor={`port_type_${portComboboxID}`}
                    requiredField={false}
                  />
                  <Select
                    id="port-select"
                    name="port-select"
                    defaultValue={getPortTypeDefaultValue(index, "non_fed_funded")}
                    onChange={(e) => handleNonFedPortTypeChange(e.target.value, index)}
                  >
                    <option value=""> - Select - </option>
                    <option value="L2">L2</option>
                    <option value="DCFC">DCFC</option>
                  </Select>
                </Grid>
                <Grid>
                  <Button
                    type="button"
                    unstyled
                    className="remove-button padding-105 text-center"
                    onClick={() => handleRemoveNonFedFundedPort(portComboboxID)}
                  >
                    Remove
                  </Button>
                </Grid>
              </Grid>
            </Grid>
          ))}

          <Button outline className="form-add-button" type="button" onClick={handleAddNonFedFundedPortChange}>
            Add Port
          </Button>
        </Grid>
      </div>
    );
  }

  /**
   * Form section for station profile information (module 1)
   * @returns the step to fill out station location information
   */
  function StationProfileInformation() {
    return (
      <div>
        <Grid row>
          <Grid col={8} className="station-profile">
            <h2 className="station-form-header"> {`Step ${isDRUser() ? "1" : "2"}: Station Profile`} </h2>
            <p>
              {" "}
              A charging station is the area in the immediate vicinity of a group of chargers and includes the chargers,
              supporting equipment, parking areas adjacent to the chargers, and lanes for vehicle ingress and egress. A
              charging station could comprise only part of the property on which it is located.
              <br />
              <br />
              Enter the identifying station information below.
            </p>
          </Grid>
        </Grid>
        <Grid row gap>
          <Grid col={5} className="form-field">
            <FormLabelAndTooltip
              formLabel="Station Nickname"
              tooltipLabel="Create a Station Nickname that is easy to remember and distinguishes this station from others. This should be created by the Direct Funding Recipients. If a nickname is given, the Station Nickname will be shown alongside the Station ID throughout EV-ChART."
              htmlFor="stationNickname"
              requiredField={false}
            />
            <CharacterCount
              id="stationNickname"
              name="stationNickname"
              type="text"
              maxLength={characterLimits["nickname"]}
              className={inputValid(invalidField.nickname, "field")}
              value={stationValues.nickname}
              onChange={(e: any) => updateField("nickname", e.target.value)}
            />
          </Grid>
        </Grid>

        <Grid row gap>
          <Grid col={5} className="form-field">
            <FormLabelAndTooltip
              formLabel="Station ID"
              tooltipLabel="This uniquely identifies a charging station. This should be created by the Network Provider and per 23 CFR 680.112, this must be the same charging station identifier used to identify the charging station in data made available to third-parties in § 680.116(c)(1)."
              htmlFor="station_id"
              requiredField={true}
            />
            <CharacterCount
              id="station_id"
              name="station_id"
              type="text"
              maxLength={characterLimits["station_id"]}
              value={stationValues.station_id}
              className={inputValid(invalidField.station_id, "field")}
              onChange={(e: SyntheticEvent<HTMLInputElement>) =>
                updateField("station_id", (e.target as HTMLInputElement).value)
              }
            />
          </Grid>
        </Grid>

        <Grid row gap>
          <Grid col={5}>
            {duplicateStationError ? (
              <ErrorMessage>The combination of this Station ID and Network Provider is already in use.</ErrorMessage>
            ) : (
              <>
                {missingRequiredMessage.station_id && !customErrors.station_id && (
                  <ErrorMessage>This field is required</ErrorMessage>
                )}
                {customErrors.station_id && (
                  <ErrorMessage>Please enter a Station ID in the correct format</ErrorMessage>
                )}
              </>
            )}
          </Grid>
        </Grid>

        <Grid row gap>
          <Grid col={5} className="form-field">
            <FormLabelAndTooltip
              formLabel="Station Address"
              tooltipLabel="Addresses may require unique formatting. Refer to EV-ChART Data Format and Preparation Guidance for examples."
              htmlFor="stationAddress"
              requiredField={true}
            />
            <TextInput
              id="stationAddress"
              name="stationAddress"
              type="text"
              className={inputValid(invalidField.address, "field")}
              value={stationValues.address}
              onChange={(e) => updateField("address", e.target.value)}
            />
            {missingRequiredMessage.address && !customErrors.address && (
              <ErrorMessage>This field is required</ErrorMessage>
            )}
            {customErrors.address && <ErrorMessage>Do not exceed 255 characters</ErrorMessage>}
          </Grid>
        </Grid>

        <Grid row gap>
          <Grid col={5} className="form-field">
            <FormLabelAndTooltip formLabel="Station City" htmlFor="stationCity" requiredField={true} />
            <TextInput
              id="stationCity"
              name="stationCity"
              type="text"
              className={inputValid(invalidField.city, "field")}
              value={stationValues.city}
              onChange={(e) => updateField("city", e.target.value)}
            />

            {missingRequiredMessage.city && !customErrors.city && <ErrorMessage>This field is required</ErrorMessage>}
            {customErrors.city && <ErrorMessage>Do not exceed 100 characters</ErrorMessage>}
          </Grid>
        </Grid>

        {stateList && (
          <Grid row gap>
            <Grid col={3} className="form-field">
              <FormLabelAndTooltip formLabel="Station State" htmlFor="state" requiredField={true} />
              {(stationValues.state !== "undefined" || !editMode) && (
                <SelectOpt
                  id="state"
                  name="state"
                  className={inputValid(invalidField.state, "field")}
                  options={stateList}
                  defaultValue={stationValues.state}
                  onChange={(e) => updateStateChoice(e)}
                />
              )}
              {missingRequiredMessage.state && <ErrorMessage>This field is required</ErrorMessage>}
            </Grid>
          </Grid>
        )}

        <Grid row gap>
          <Grid col={3} className="form-field">
            <FormLabelAndTooltip formLabel="Station ZIP" htmlFor="stationZIP" requiredField={true} />
            <CharacterCount
              id="stationZIP"
              name="stationZIP"
              type="text"
              maxLength={characterLimits["zip"]}
              value={stationValues.zip}
              className={inputValid(invalidField.zip, "field")}
              onChange={(e: any) => updateField("zip", e.target.value)}
            />
            {missingRequiredMessage.zip && !customErrors.zip && <ErrorMessage>This field is required</ErrorMessage>}
            {customErrors.zip && <ErrorMessage>Use numerical characters only</ErrorMessage>}
          </Grid>
          <Grid col={3} className="form-field">
            <FormLabelAndTooltip formLabel="Station ZIP Extended" htmlFor="stationExtended" requiredField={true} />
            <CharacterCount
              id="stationZIPExtended"
              name="stationZIPExtended"
              type="text"
              maxLength={characterLimits["zip_extended"]}
              value={stationValues.zip_extended}
              className={inputValid(invalidField.zip_extended, "field")}
              onChange={(e: SyntheticEvent<HTMLInputElement>) =>
                updateField("zip_extended", (e.target as HTMLInputElement).value)
              }
            />
            {missingRequiredMessage.zip_extended && !customErrors.zip_extended && (
              <ErrorMessage>This field is required</ErrorMessage>
            )}
            {customErrors.zip_extended && <ErrorMessage>Use numerical characters only</ErrorMessage>}
          </Grid>
        </Grid>

        <Grid row gap>
          <Grid col={5} className="form-field">
            <FormLabelAndTooltip
              formLabel="Station Latitude"
              tooltipLabel="Latitude of the charging station location, derived based on point placement and in decimal degrees. A charging station could comprise only part of the property on which it is located. Provide the latitude specifically of the charging station rather than that of the parcel on which it is located. This number must be between 90 and -90 with 6 or more decimal places. "
              htmlFor="stationLatitude"
              requiredField={true}
            />
            <TextInput
              id="stationLatitude"
              name="stationLatitude"
              type="text"
              className={inputValid(invalidField.latitude, "field")}
              value={stationValues.latitude}
              onChange={(e) => updateField("latitude", e.target.value)}
            />
            <div className="usa-hint station-registration-hint">
              Number with 6 or more decimal places between 90 and -90
            </div>
            {missingRequiredMessage.latitude && !customErrors.latitude && (
              <ErrorMessage>This field is required</ErrorMessage>
            )}
            {customErrors.latitude && (
              <ErrorMessage>Use a maximum of 10 digits, between 90 and -90 with 6 or more decimal places</ErrorMessage>
            )}
          </Grid>
        </Grid>

        <Grid row gap>
          <Grid col={5} className="form-field">
            <FormLabelAndTooltip
              formLabel="Station Longitude"
              tooltipLabel="Longitude of the charging station location, derived based on point placement and in decimal degrees. A charging station could comprise only part of the property on which it is located. Provide the longitude specifically of the charging station rather than that of the parcel on which it is located. This number must be between 180 and -180 with 6 or more decimal places. "
              htmlFor="stationLongitude"
              requiredField={true}
            />
            <TextInput
              id="stationLongitude"
              name="stationLongitude"
              type="text"
              className={inputValid(invalidField.longitude, "field")}
              value={stationValues.longitude}
              onChange={(e) => updateField("longitude", e.target.value)}
            />
            <div className="usa-hint station-registration-hint">
              Number with 6 or more decimal places between 180 and -180
            </div>
            {missingRequiredMessage.longitude && !customErrors.longitude && (
              <ErrorMessage>This field is required</ErrorMessage>
            )}
            {customErrors.longitude && (
              <ErrorMessage>
                Use a maximum of 11 digits, between 180 and -180 with 6 or more decimal places
              </ErrorMessage>
            )}
          </Grid>
        </Grid>

        {networkProvidersList.length > 0 && (
          <Grid row gap>
            <Grid col={5} className="form-field">
              <FormLabelAndTooltip
                formLabel="Network Provider"
                tooltipLabel={`The Network Provider is the entity that operates the digital communication network that remotely manages the chargers. Charging network providers may also serve as charging station operators and/or manufacture chargers. If the Network Provider of this station is not found in the selection list, please select “Other”.`}
                htmlFor="input-network_provider"
                requiredField={true}
              />
              {(defaultNetworkProvider || !editMode) && (
                <ComboBox
                  className={inputValid(invalidField.network_provider, "combobox")}
                  id="input-network-provider"
                  name="input-network-provider"
                  defaultValue={defaultNetworkProvider}
                  options={networkProvidersList}
                  onChange={(e) => {
                    handleNetworkProviderChange(e);
                  }}
                />
              )}
              {duplicateStationError ? (
                <ErrorMessage>The combination of this Station ID and Network Provider is already in use.</ErrorMessage>
              ) : (
                missingRequiredMessage.network_provider && <ErrorMessage>This field is required</ErrorMessage>
              )}
            </Grid>
          </Grid>
        )}

        {!RegisterNonFedFundedStationFeatureFlag && (
          <Grid row gap>
            <Grid col={5} className="form-field">
              <FormLabelAndTooltip
                formLabel="Project Type"
                tooltipLabel={`The Project Type describes how the federal funds are being spent. Select "Install a New Station" for any station that was newly built using federal funds. Select "Update an existing station" for any station that already existed but used federal funds to be repaired, replaced, or upgraded to be compliant. Select "Only Provide O&M" for any station where federal funds are only used for operation and maintenance.`}
                htmlFor="input-ProjectType"
                requiredField={true}
              />
              <Select
                id="input-select"
                name="input-select"
                className={inputValid(invalidField.project_type, "field")}
                value={stationValues.project_type}
                onChange={(e) => updateField("project_type", e.target.value)}
              >
                <option value=""> - Select - </option>
                <option value="new_station">Install a new station</option>
                <option value="existing_station">Update an existing station</option>
                <option value="o_and_m">Only provide operation and maintenance (O&M)</option>
              </Select>
              {missingRequiredMessage.project_type && <ErrorMessage>This field is required</ErrorMessage>}
            </Grid>
          </Grid>
        )}

        <Grid row gap>
          <Grid col={5} className="form-field">
            <FormLabelAndTooltip
              formLabel="Operational Date"
              tooltipLabel={`The date the station officially became operational. By providing this information, EV-ChART can provide users with accurate visualizations of data submission tracking for each Station ID.`}
              htmlFor="input-operational-date"
              requiredField={true}
            />

            {defaultOperationalDate && (
              <DatePicker
                id="operational-date"
                name="operational-date"
                defaultValue={defaultOperationalDate}
                aria-describedby="operational-date-hint"
                aria-labelledby="operational-date-label"
                className={inputValid(invalidField.operational_date, "datepicker")}
                onChange={(e) => updateOperationalDate(e)}
              />
            )}
            <div className="usa-hint station-registration-hint" id="appointment-date-hint">
              mm/dd/yyyy
            </div>
            {missingRequiredMessage.operational_date && !customErrors.operational_date && (
              <ErrorMessage>This field is required</ErrorMessage>
            )}
            {customErrors.operational_date && <ErrorMessage>Please enter a date in the correct format</ErrorMessage>}
          </Grid>
        </Grid>
        <>
          {!RegisterNonFedFundedStationFeatureFlag && (
            <div>
              <Grid row gap>
                <Grid col={5} className="form-field">
                  <FormLabelAndTooltip
                    formLabel="Funding Type"
                    tooltipLabel={`Federal funding program(s) directing funds to a project associated with a station.`}
                    htmlFor="input-FundingType"
                    requiredField={true}
                  />

                  {missingRequiredMessage.funding_type && <ErrorMessage>This field is required</ErrorMessage>}
                </Grid>
              </Grid>

              <Grid row gap>
                <Grid col={2} className="form-field funding-type-options">
                  {fundingOptionsListLeft.map((option) => (
                    <Checkbox
                      id={`fundingTypeOption${option.name}`}
                      name="checkbox"
                      key={`fundingTypeOption${option.name}`}
                      label={
                        <div className="label-tooltip-container">
                          {option.name.replace("_", "-")}
                          <Tooltip label={option.description} asCustom={CustomLink}>
                            <Icon.InfoOutline className="tooltip-icon" />
                          </Tooltip>
                        </div>
                      }
                      checked={stationValues[option.name as keyof StationAddNew] === 1}
                      onChange={() => handleFundingTypeChange(option.name.toUpperCase() as keyof StationAddNew)}
                    />
                  ))}
                </Grid>
                <Grid col={3} className="form-field funding-type-options">
                  {fundingOptionsListRight.map((option) => (
                    <Checkbox
                      id={`fundingTypeOption${option.name}`}
                      name="checkbox"
                      key={`fundingTypeOption${option.name}`}
                      label={
                        <div className="label-tooltip-container">
                          {option.name === "OTHER" ? "Other - Not Listed" : option.name}
                          <Tooltip label={option.description} asCustom={CustomLink}>
                            <Icon.InfoOutline className="tooltip-icon" />
                          </Tooltip>
                        </div>
                      }
                      checked={stationValues[option.name as keyof StationAddNew] === 1}
                      onChange={() => handleFundingTypeChange(option.name.toUpperCase() as keyof StationAddNew)}
                    />
                  ))}
                </Grid>
              </Grid>
            </div>
          )}

          <Grid row gap>
            <Grid col={5} className="form-field">
              <FormLabelAndTooltip
                formLabel="Station Located on AFC"
                tooltipLabel={`Indicator for if this charging station is located along and designed to serve the users of Alternative Fuel Corridors.`}
                htmlFor="input-AFC"
                requiredField={true}
              />
              {missingRequiredMessage.AFC && <ErrorMessage>This field is required</ErrorMessage>}
            </Grid>
          </Grid>

          {defaultAFC !== undefined && (
            <Grid row gap>
              <Fieldset legendStyle="srOnly">
                <Radio
                  id="input-yes-radio"
                  name="input-afc-radio"
                  className="afc-radio-field"
                  label="Yes"
                  value="1"
                  onChange={(e) => updateAFCField(e.target.value)}
                  defaultChecked={defaultAFC === 1}
                />
                <Radio
                  id="input-no-radio"
                  name="input-afc-radio"
                  className="afc-radio-field"
                  label="No"
                  value="0"
                  onChange={(e) => updateAFCField(e.target.value)}
                  defaultChecked={defaultAFC === 0}
                />
              </Fieldset>
            </Grid>
          )}
        </>
      </div>
    );
  }

  /**
   * Step 2 for verifying federal funding status
   * @returns the step to fill out federally funded, funding type, and project type
   */
  function ProjectInformation() {
    return (
      <div>
        <Grid row>
          <Grid col={8} className="station-profile">
            <h2 className="station-form-header"> {`Step ${isDRUser() ? "2" : "3"}: Federal Funding Status`} </h2>
            <p>
              {" "}
              A charging station is considered to be federally funded if using funds made available under Title 23,
              U.S.C. for projects for the construction of publicly accessible EV chargers or any EV charging
              infrastructure project funded with Federal funds that is treated as a project on a Federal-aid highway.
              This includes any use of these funds for the acquisition, installation, network connection, operation, or
              maintenance of this charging station.
            </p>
          </Grid>
        </Grid>
        {RegisterNonFedFundedStationFeatureFlag &&
        (!editMode || (defaultFederallyFunded !== undefined && editMode === true)) ? (
          <div>
            <Grid row gap>
              <Grid col={5} className="form-field">
                <FormLabelAndTooltip
                  formLabel="Federally Funded"
                  tooltipLabel={`The acquisition, installation, network connection, operation, or maintenance of this charging station, uses NEVI Formula Program funds, funds made available under Title 23, U.S.C. for projects for the construction of publicly accessible EV chargers, or any EV charging infrastructure project funded with Federal funds that is treated as a project on a Federal-aid highway.`}
                  htmlFor="input-station-uses-federal-funds"
                  requiredField={true}
                />
                {missingRequiredMessage.federally_funded && <ErrorMessage>This field is required</ErrorMessage>}
                <Fieldset legendStyle="srOnly">
                  <Radio
                    id="input-yes-radio-funded"
                    name="input-federally-funded-radio"
                    className="federally-funded-radio-field"
                    label="Yes"
                    value="1"
                    onChange={(e) => handleIsStationFederallyFunded(e.target.value)}
                    defaultChecked={defaultFederallyFunded === true}
                  />
                  <Radio
                    id="input-no-radio-not-funded"
                    name="input-federally-funded-radio"
                    className="federally-funded-radio-field"
                    label="No"
                    value="0"
                    onChange={(e) => handleIsStationFederallyFunded(e.target.value)}
                    defaultChecked={defaultFederallyFunded === false}
                  />
                </Fieldset>
              </Grid>
            </Grid>
            {isStationFederallyFunded && FundingTypeOptions()}
          </div>
        ) : (
          FundingTypeOptions()
        )}

        <Grid row gap>
          <Grid col={5} className="form-field">
            <FormLabelAndTooltip
              formLabel="Project Type"
              tooltipLabel={`The Project Type describes how the federal funds are being spent. Select "Install a New Station" for any station that was newly built using federal funds. Select "Update an existing station" for any station that already existed but used federal funds to be repaired, replaced, or upgraded to be compliant. Select "Only Provide O&M" for any station where federal funds are only used for operation and maintenance.`}
              htmlFor="input-ProjectType"
              requiredField={true}
            />
            <Select
              id="input-select"
              name="input-select"
              className={inputValid(invalidField.project_type, "field")}
              value={stationValues.project_type}
              onChange={(e) => updateField("project_type", e.target.value)}
            >
              <option value=""> - Select - </option>
              <option value="new_station">Install a new station</option>
              <option value="existing_station">Update an existing station</option>
              <option value="o_and_m">Only provide operation and maintenance (O&M)</option>
            </Select>
            {missingRequiredMessage.project_type && <ErrorMessage>This field is required</ErrorMessage>}
          </Grid>
        </Grid>
      </div>
    );
  }

  /**
   * Step 2 for direct recipients creating a new station
   * @returns form section for them to authorize one or multiple subrecipients to their station
   */
  function DRAuthorizesSubrecipients(): React.ReactNode {
    return (
      <>
        <Grid row col={8}>
          <h2 className="station-form-header">
            {" "}
            {`Step ${!RegisterNonFedFundedStationFeatureFlag ? "2" : "3"}: Authorize Subrecipient(s)/Contractor(s)`}{" "}
          </h2>
          <p>
            Would you like to authorize a subrecipient to submit data for this station on your behalf? If you do not
            authorize a subrecipient to submit data on your behalf, you will be required to submit data directly.
            <br />
            <br />
            If the subrecipient you&apos;d like to authorize is not in our system, you can add and authorize it later in
            the Subrecipients page under the Management tab.
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
                    Subrecipient
                  </Label>
                  <ComboBox
                    id={`input-subrecipient${subRecipientComboboxId}`}
                    name={`input-subrecipient${subRecipientComboboxId}`}
                    options={subRecipientsList}
                    className={checkEntriesError("subrecipient", subRecipientComboboxId)}
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
   * Step 1 for sub recipient creating a new station
   * @returns form section for sub recipient to selection the associated direct recipient
   */
  function SRRequestAuthorization(): React.ReactNode {
    return (
      <>
        <Grid row col={8}>
          <h2 className="station-form-header"> Step 1: Select Direct Funding Recipient for Station </h2>
          <p>
            You must identify the Direct Recipient that will be associated with this station.
            <br />
            <br />
            Once you add the station, your direct recipient will need to approve the station. Once approved, you will be
            able to submit data for this station on behalf of the direct recipient. Direct recipients manage all
            authorizations and final data approvals for this station.
          </p>
        </Grid>

        {renderDRSelectionOptions ? (
          <Grid className="organization-selection-combobox">
            <Grid row>
              <Grid col={5}>
                <Label htmlFor="direct-recipient" className="required-field">
                  Direct Recipient Organization
                </Label>
                <ComboBox
                  className={inputValid(invalidField.dr_id, "combobox")}
                  id={`input-direct-recipient`}
                  name={`input-direct-recipient`}
                  options={directRecipientsList}
                  onChange={(e) => updateField("dr_id", e)}
                />
              </Grid>
              <Grid></Grid>
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

        {missingRequiredMessage.dr_id && <ErrorMessage>This field is required</ErrorMessage>}
      </>
    );
  }

  return (
    <>
      <div className="stationRegistration">
        <div>
          <GridContainer>
            <DefaultBreadcrumb />
          </GridContainer>
        </div>
        <div className="usa-section" style={{ paddingTop: 0 }}>
          <GridContainer>
            {incorrectValues.length > 0 && (
              <Alert type="error" headingLevel="h3" heading="Please correct the following fields:">
                <ul>
                  {incorrectValues.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </Alert>
            )}
            {unableToDeletePortError && (
              <Alert type="error" headingLevel="h3" heading="Cannot delete ports with data:">
                <ul>
                  {portsWithData.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </Alert>
            )}

            <Grid col={12}>{editMode ? <h1> Edit Station </h1> : <h1> Add Station </h1>}</Grid>
            {isUploadingData ? (
              <GridContainer>
                <Grid row>
                  <Grid col className="spinner-content">
                    <Spinner></Spinner>
                  </Grid>
                </Grid>
              </GridContainer>
            ) : (
              <>
                {isDRUser() ? (
                  <>
                    {StationProfileInformation()}
                    {RegisterNonFedFundedStationFeatureFlag && ProjectInformation()}
                    {DRAuthorizesSubrecipients()}
                  </>
                ) : (
                  <>
                    {SRRequestAuthorization()}
                    {StationProfileInformation()}
                    {RegisterNonFedFundedStationFeatureFlag && ProjectInformation()}
                  </>
                )}

                {PortInformation()}
              </>
            )}
            <Grid row gap className="form-submit-button-group">
              <ButtonGroup>
                {editMode ? (
                  <Button type="button" onClick={handleSaveStation} disabled={isUploadingData}>
                    {stationValues.status === "Active" ? "Save" : "Save & Add Station"}
                  </Button>
                ) : (
                  <Button
                    type="button"
                    disabled={isUploadingData}
                    onClick={recipientType === "direct-recipient" ? handleAddStation : handleSRAddStation}
                  >
                    Add Station
                  </Button>
                )}
                <Button
                  onClick={openModal}
                  disabled={isUploadingData}
                  type="button"
                  unstyled
                  className="padding-105 text-center"
                >
                  Cancel
                </Button>
              </ButtonGroup>
            </Grid>
            {isRemovePortsConfirmationModalOpen && (
              <RemovePortConfirmationModal
                onClose={closeRemovePortsConfirmationModal}
                onConfirm={confirmAndCloseRemovePortsConfirmationModal}
                station_name={stationValues.station_id}
                ports_to_remove={selectedFedFundedPorts}
                setIsStationFederallyFunded={setIsStationFederallyFunded}
              />
            )}
          </GridContainer>

          {isSRSubmitModalOpen && SRAddsStationFeatureFlag && (
            <SRAddStationModal
              stationValues={stationValues}
              directRecipient={getDRNameById(stationValues.dr_id)}
              handleAddStation={handleAddStation}
              onClose={closeSRAddStationModal}
            />
          )}

          {isCancelModalOpen && <CancelModal navigateUrl={ROUTE_STATIONS} onClose={closeModal} />}
        </div>
      </div>
    </>
  );
}

export default StationForm;
