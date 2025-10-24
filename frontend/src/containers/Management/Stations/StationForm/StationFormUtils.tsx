/**
 * Helper functions used in station registration.
 * @packageDocumentation
 **/
import { CharacterMapping, StationAddNew, PortsInfo } from "../../../../interfaces/Stations/stations-interface";

/**
 * Character limits for fields in station registration
 */
export const characterLimits: CharacterMapping = {
  nickname: 50,
  station_id: 36,
  address: 255,
  city: 100,
  zip: 5,
  zip_extended: 4,
  num_fed_funded_ports: 3,
  num_non_fed_funded_ports: 3,
  port_id: 36,
};

/**
 * Function to convert date format
 * @param dateString unformatted date string
 * @returns correctly formatted date
 */
export function convertDateFormat(dateString: string): string {
  const [month, day, year] = dateString.split("/");

  if (!month || !day || !year) {
    return dateString;
  }

  const paddedMonth = month.padStart(2, "0");
  const paddedDay = day.padStart(2, "0");

  const formattedDate = `${year}-${paddedMonth}-${paddedDay}`;
  return formattedDate;
}

/**
 * Function to determine if a passed date is in valid format/ exists
 * @param dateString the date as a string
 * @returns boolean for if date is valid
 */
const isValidDate = (dateString: string): boolean => {
  const validPattern = /^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$/;
  if (!validPattern.test(dateString)) {
    return false;
  }

  const [year, month, day] = dateString.split("-").map(Number);

  const date = new Date(year, month - 1, day);

  if (date.getFullYear() !== year || date.getMonth() !== month - 1 || date.getDate() !== day) {
    return false;
  }
  return true;
};

/**
 * Function to determine if an array contains duplicate values
 * @param arr the array to check
 * @returns bool if the arr contains duplicates
 */
function hasDuplicateValues(arr: string[]): boolean {
  const uniqueValues = new Set<string>();
  for (const item of arr) {
    if (item !== undefined) {
      if (uniqueValues.has(item.trim())) {
        return true;
      }
      uniqueValues.add(item.trim());
    }
  }
  return false;
}

/**
 * Function to set class name based on if field data is valid/ invalid
 * @param field boolean if the field contains an error
 * @param type the type of field in the ui form
 * @returns the appropriate class name
 */
export function inputValid(field: boolean, type: string): string {
  if (field && type === "combobox") {
    return "error-combobox";
  } else if (field && type === "datepicker") {
    return "error-datepicker";
  } else if (field) {
    return "usa-input--error";
  } else {
    return "";
  }
}

/**
 * Function to check through inputted fields to determine if data is valid / correct format
 * @returns boolean if all provided station data is valid
 */
export function checkValidData(
  stationValues: StationAddNew,
  customErrors: { [key: string]: boolean } = {},
  invalidField: { [key: string]: boolean } = {},
  missingRequiredMessage: { [key: string]: boolean } = {},
  featureFlags: { [key: string]: boolean },
  duplicateStationError: boolean,
  selectedSubrecipients: string[],
  authorizeSubrecipients: number[],
  selectedFedFundedPorts: PortsInfo[],
  selectedNonFedFundedPorts: PortsInfo[],
  fedFundedPorts: number[],
  nonFedFundedPorts: number[],
  isStationFederallyFunded: boolean | null,
  setIncorrectValues: React.Dispatch<React.SetStateAction<string[]>>,
  setErrorSubrecipients: React.Dispatch<React.SetStateAction<number[]>>,
  setErrorPortIDs: React.Dispatch<React.SetStateAction<number[]>>,
  setInvalidField: React.Dispatch<React.SetStateAction<{ [key: string]: boolean }>>,
  setMissingRequiredMessage: React.Dispatch<React.SetStateAction<{ [key: string]: boolean }>>,
  setCustomErrors: React.Dispatch<React.SetStateAction<{ [key: string]: boolean }>>,
): boolean {
  //resetting incorrect values when data is re-checked
  setIncorrectValues([]);

  const updatedCustomErrors = { ...customErrors };
  const updatedinvalidField = { ...invalidField };
  const updatedMissingRequiredMessage = { ...missingRequiredMessage };

  //Regex for no spaces
  const validStationID = /^\S+$/.test(stationValues.station_id);
  const stationIDValue = stationValues.station_id.trim();
  const exceededStationIdCharacters = stationValues.station_id.length > characterLimits["station_id"];
  if (stationIDValue === "" || !validStationID || exceededStationIdCharacters) {
    updatedinvalidField.station_id = true;
    setIncorrectValues((prevArray) => [...prevArray, "Station ID"]);
    if (stationIDValue === "" || !validStationID) {
      updatedMissingRequiredMessage.station_id = true;
    }
    if (!validStationID && stationIDValue !== "") {
      updatedCustomErrors.station_id = true;
    }
  }

  if (duplicateStationError) {
    setIncorrectValues((prevArray) => [...prevArray, "Station ID", "Network Provider"]);
  }

  const exceededNicknameCharacters = stationValues.nickname.length > characterLimits["nickname"];
  if (exceededNicknameCharacters) {
    updatedinvalidField.nickname = true;
    updatedCustomErrors.nickname = true;
    setIncorrectValues((prevArray) => [...prevArray, "Nickname"]);
  }

  const exceededAddressCharacters = stationValues.address.length > characterLimits["address"];
  const addressValue = stationValues.city.trim();
  if (addressValue === "" || exceededAddressCharacters) {
    updatedinvalidField.address = true;
    updatedMissingRequiredMessage.address = true;
    setIncorrectValues((prevArray) => [...prevArray, "Station Address"]);
    if (exceededAddressCharacters) {
      updatedCustomErrors.address = true;
    }
  }

  const exceededCityCharacters = stationValues.city.length > characterLimits["city"];
  const cityValue = stationValues.city.trim();
  if (cityValue === "" || exceededCityCharacters) {
    updatedinvalidField.city = true;
    updatedMissingRequiredMessage.city = true;
    setIncorrectValues((prevArray) => [...prevArray, "Station City"]);
    if (exceededCityCharacters) {
      updatedCustomErrors.city = true;
    }
  }

  if (stationValues.state === undefined || stationValues.state === "undefined" || stationValues.state === "") {
    updatedinvalidField.state = true;
    updatedMissingRequiredMessage.state = true;
    setIncorrectValues((prevArray) => [...prevArray, "Station State"]);
  }

  //Regex for 5 digits
  const validZip = /^\d{5}$/.test(stationValues.zip);
  const zipValue = stationValues.zip.trim();
  if (zipValue === "" || !validZip) {
    updatedinvalidField.zip = true;
    updatedMissingRequiredMessage.zip = true;
    setIncorrectValues((prevArray) => [...prevArray, "Station Zip"]);
    if (!validZip && zipValue !== "") {
      updatedCustomErrors.zip = true;
    }
  }

  //Regex for 4 digits
  const validZipExtended = /^\d{4}$/.test(stationValues.zip_extended);
  const zipExtendedValue = stationValues.zip_extended.trim();
  if (zipExtendedValue === "" || !validZipExtended) {
    updatedinvalidField.zip_extended = true;
    updatedMissingRequiredMessage.zip_extended = true;
    setIncorrectValues((prevArray) => [...prevArray, "Station Zip Extended"]);
    if (!validZipExtended && zipExtendedValue !== "") {
      updatedCustomErrors.zip_extended = true;
    }
  }

  const latArray = stationValues.latitude.split(".");
  const validLatitude = latArray[1] && latArray[1].length >= 6 && latArray[1].length < 9; // VERIFY THESE VALUES
  const latitudeValue = stationValues.latitude.trim();
  const latitudeOutsideRange = Number(latitudeValue) > 90 || Number(latitudeValue) < -90;
  const latitudeNumCheck = Number.isNaN(Number(latitudeValue));
  if (latitudeValue === "" || !validLatitude || latitudeOutsideRange || latitudeNumCheck) {
    updatedinvalidField.latitude = true;
    updatedMissingRequiredMessage.latitude = true;
    setIncorrectValues((prevArray) => [...prevArray, "Station Latitude"]);
    if ((!validLatitude || latitudeOutsideRange || latitudeNumCheck) && latitudeValue !== "") {
      updatedCustomErrors.latitude = true;
    }
  }

  const lonArray = stationValues.longitude.split(".");
  const validLongitude = lonArray[1] && lonArray[1].length >= 6 && lonArray[1].length < 9; // VERIFY THESE VALUES
  const longitudeValue = stationValues.longitude.trim();
  const longitudeOutsideRange = Number(longitudeValue) > 180 || Number(longitudeValue) < -180;
  const longitudeNumCheck = Number.isNaN(Number(longitudeValue));
  if (longitudeValue === "" || !validLongitude || longitudeOutsideRange || longitudeNumCheck) {
    updatedinvalidField.longitude = true;
    updatedMissingRequiredMessage.longitude = true;
    setIncorrectValues((prevArray) => [...prevArray, "Station Longitude"]);
    if ((!validLongitude || longitudeOutsideRange || longitudeNumCheck) && longitudeValue !== "") {
      updatedCustomErrors.longitude = true;
    }
  }

  if (stationValues.network_provider === undefined) {
    updatedinvalidField.network_provider = true;
    updatedMissingRequiredMessage.network_provider = true;
    setIncorrectValues((prevArray) => [...prevArray, "Network Provider"]);
  }

  if (stationValues.project_type.trim() === "") {
    updatedinvalidField.project_type = true;
    updatedMissingRequiredMessage.project_type = true;
    setIncorrectValues((prevArray) => [...prevArray, "Project Type"]);
  }

  const operationalDateValue = stationValues.operational_date && stationValues.operational_date.replace(/\s/g, "");
  const dateValid = isValidDate(operationalDateValue);
  if ((stationValues.operational_date !== null && operationalDateValue === "") || !dateValid) {
    updatedinvalidField.operational_date = true;
    updatedMissingRequiredMessage.operational_date = true;
    if (!dateValid) {
      updatedCustomErrors.operational_date = true;
    }
    setIncorrectValues((prevArray) => [...prevArray, "Operational Date"]);
  }

  if (
    stationValues.NEVI === 0 &&
    stationValues.CFI === 0 &&
    stationValues.EVC_RAA === 0 &&
    stationValues.CMAQ === 0 &&
    stationValues.CRP === 0 &&
    stationValues.OTHER === 0
  ) {
    // set funding type error to false if station is not federally funded and ft is on
    if (featureFlags.RegisterNonFedFundedStationFeatureFlag && !isStationFederallyFunded) {
      updatedinvalidField.funding_type = false;
      updatedMissingRequiredMessage.funding_type = true;
    } else {
      updatedinvalidField.funding_type = true;
      updatedMissingRequiredMessage.funding_type = true;
      setIncorrectValues((prevArray) => [...prevArray, "Funding Type"]);
    }
  }

  if (stationValues.dr_id === undefined && featureFlags.SRAddsStationFeatureFlag) {
    updatedinvalidField.dr_id = true;
    updatedMissingRequiredMessage.dr_id = true;
    setIncorrectValues((prevArray) => [...prevArray, "Direct Recipient"]);
  }

  if (stationValues.AFC === undefined) {
    updatedinvalidField.AFC = true;
    updatedMissingRequiredMessage.AFC = true;
    setIncorrectValues((prevArray) => [...prevArray, "Station Located on AFC"]);
  }

  if (stationValues.federally_funded === null) {
    updatedinvalidField.federally_funded = true;
    updatedMissingRequiredMessage.federally_funded = true;
    setIncorrectValues((prevArray) => [...prevArray, "Federally Funded"]);
  }

  // if station is federally funded, evaluate fed_funded_ports as required fields, while non_fed_funded_ports as not required
  if (
    featureFlags.RegisterNonFedFundedStationFeatureFlag === false ||
    (featureFlags.RegisterNonFedFundedStationFeatureFlag === true && isStationFederallyFunded !== false)
  ) {
    portValidation(
      true, //isRequiredField
      "num_fed_funded_ports",
      "fed_funded_ports",
      stationValues,
      updatedCustomErrors,
      updatedinvalidField,
      updatedMissingRequiredMessage,
      setIncorrectValues,
    );

    portValidation(
      false, //isRequiredField
      "num_non_fed_funded_ports",
      "non_fed_funded_ports",
      stationValues,
      updatedCustomErrors,
      updatedinvalidField,
      updatedMissingRequiredMessage,
      setIncorrectValues,
    );
  }
  // if station is not federally funded, only evaluate the non_fed_funded_ports as requried fields
  if (featureFlags.RegisterNonFedFundedStationFeatureFlag === true && isStationFederallyFunded === false) {
    portValidation(
      true, //isRequiredField
      "num_non_fed_funded_ports",
      "non_fed_funded_ports",
      stationValues,
      updatedCustomErrors,
      updatedinvalidField,
      updatedMissingRequiredMessage,
      setIncorrectValues,
    );

    portValidation(
      false, //isRequiredField
      "num_fed_funded_ports",
      "fed_funded_ports",
      stationValues,
      updatedCustomErrors,
      updatedinvalidField,
      updatedMissingRequiredMessage,
      setIncorrectValues,
    );
  }

  //subrecipient dropdown with unselected subrecipients
  const hasUndefinedSubrecipients = selectedSubrecipients.some((item) => item === undefined);
  const hasDuplicateSubrecipients = hasDuplicateValues(selectedSubrecipients);
  if (hasUndefinedSubrecipients || hasDuplicateSubrecipients) {
    updatedinvalidField.authorized_subrecipients = true;
    updatedMissingRequiredMessage.authorized_subrecipients = true;
    updatedCustomErrors.authorized_subrecipients = true;
    setIncorrectValues((prevArray) => [...prevArray, "Authorized Subrecipients"]);
    setErrorSubrecipients(findUndefinedOrRepetitiveIndicies(selectedSubrecipients, authorizeSubrecipients));
  }

  const portErrors = findUndefinedOrRepetitivePortEntries(
    selectedFedFundedPorts,
    selectedNonFedFundedPorts,
    fedFundedPorts,
    nonFedFundedPorts,
  );
  if (portErrors.errors.length > 0) {
    if (portErrors.fed) {
      updatedinvalidField.fed_funded_ports = true;
      updatedMissingRequiredMessage.fed_funded_ports = true;
      updatedCustomErrors.fed_funded_ports = true;
      setIncorrectValues((prevArray) => [...prevArray, "Federally Funded Port IDs"]);
    }
    if (portErrors.non_fed) {
      updatedinvalidField.non_fed_funded_ports = portErrors.non_fed;
      updatedMissingRequiredMessage.non_fed_funded_ports = portErrors.non_fed;
      updatedCustomErrors.non_fed_funded_ports = portErrors.non_fed;
      setIncorrectValues((prevArray) => [...prevArray, "Non-Federally Funded Port IDs"]);
    }
    setErrorPortIDs(portErrors.errors);
  }

  //if previously attempted and received duplicate error, assume both valid to try and post again
  if (duplicateStationError) {
    updatedinvalidField.station_id = false;
    updatedinvalidField.network_provider = false;
  }

  setInvalidField(updatedinvalidField);
  setMissingRequiredMessage(updatedMissingRequiredMessage);
  setCustomErrors(updatedCustomErrors);

  return Object.values(updatedinvalidField).every((valid) => !valid);
}

/**
 * Function to determine if the provided port ids have undefined (empty) or repetetive entries
 * @returns an object with the id of all the errors, and the fed/ non-fed errors
 */
function findUndefinedOrRepetitivePortEntries(
  selectedFedFundedPorts: PortsInfo[],
  selectedNonFedFundedPorts: PortsInfo[],
  fedFundedPorts: number[],
  nonFedFundedPorts: number[],
): {
  errors: number[];
  fed: boolean;
  non_fed: boolean;
} {
  const seenIds = new Set<string>();
  const errorBoxes = new Set<number>();
  let fedErrors = false;
  let nonFedErrors = false;

  for (let i = 0; i < selectedFedFundedPorts.length; i++) {
    const entry = selectedFedFundedPorts[i];
    const box = fedFundedPorts[i];
    if (!entry.port_id || seenIds.has(entry.port_id) || entry.port_id.length > characterLimits["port_id"]) {
      errorBoxes.add(box);
      fedErrors = true;
    } else {
      seenIds.add(entry.port_id);
    }
  }

  for (let i = 0; i < selectedNonFedFundedPorts.length; i++) {
    const entry = selectedNonFedFundedPorts[i];
    const box = nonFedFundedPorts[i];
    if (!entry.port_id || seenIds.has(entry.port_id) || entry.port_id.length > characterLimits["port_id"]) {
      errorBoxes.add(box);
      nonFedErrors = true;
    } else {
      seenIds.add(entry.port_id);
    }
  }

  return {
    errors: Array.from(errorBoxes),
    fed: fedErrors,
    non_fed: nonFedErrors,
  };
}

/**
 * Function to determine if the provided sub recipients ids have undefined (unselected) or repetetive entries
 * @param arr the array to check
 * @returns the list of all undefined or repetitive entries
 */
function findUndefinedOrRepetitiveIndicies(arr: (string | undefined)[], authorizeSubrecipients: number[]): number[] {
  const seen: { [key: string]: number } = {};
  const result: number[] = [];

  for (let i = 0; i < arr.length; i++) {
    const element = arr[i]?.trim();

    if (element === undefined || seen[element] !== undefined || element.trim() === "") {
      result.push(authorizeSubrecipients[i]);
    }
    if (element !== undefined) {
      seen[element] = i;
    }
  }
  return result;
}

/**
 * Helper function that deals with extensive port validation. Enforces that port fields are required,
 * checks if port number = ports provided, and has specific error handling for different user in put edge cases
 * correctly sets the stationValues, invalidField, missingRequiredMessage, customErrors objects
 * @param isRequiredField boolean that specifies if current field is required
 * @param num_of_ports num_of_fed_funded_ports OR num_of_non_fed_funded stationValue field name
 * @param port_info fed_funded_ports or non_fed_funded_ports stationValue field name
 * @param stationValues stationValues object that holds current state of user input
 * @param updatedCustomErrors state object indicating with a boolean which stationValue fields need a custom error
 * @param updatedMissingRequriedMessage state object indicating with a boolean which stationValue fields are required but missing user input
 * @param setIncorrectValues setter for the incorrectValues state to update values after port validation
 * @returns updated state values for customErrors, invalidField, and missingRequriedMessage dependent on port validation logic
 */
export function portValidation(
  isRequiredField: boolean,
  num_of_ports: keyof StationAddNew,
  port_info: keyof StationAddNew,
  stationValues: StationAddNew,
  updatedCustomErrors: { [key: string]: boolean } = {},
  updatedinvalidField: { [key: string]: boolean } = {},
  updatedMissingRequiredMessage: { [key: string]: boolean } = {},
  setIncorrectValues: React.Dispatch<React.SetStateAction<string[]>>,
) {
  const stationValuesFieldMapping: { [key: string]: string } = {
    num_fed_funded_ports: "Number of Federally Funded Ports",
    num_non_fed_funded_ports: "Number of Non-Federally Funded Ports",
  };

  // resetting custom errors to be re-evaluated when form submits
  updatedCustomErrors[num_of_ports.concat("_zero")] = false;
  updatedCustomErrors[num_of_ports.concat("_greater_than")] = false;
  updatedCustomErrors[num_of_ports.concat("_less_than")] = false;

  let numPortsProvided = false;
  if (stationValues[num_of_ports] !== null && String(stationValues[num_of_ports]) !== "") {
    numPortsProvided = true;
  }

  let validNumberOfPorts;
  // checks if valid number of ports is provided
  if (numPortsProvided) {
    validNumberOfPorts = Number(stationValues[num_of_ports]) >= 0 && Number(stationValues[num_of_ports]) <= 999;
    // resetting required message to false if a port value was provided
    if (isRequiredField && updatedMissingRequiredMessage[num_of_ports]) {
      updatedMissingRequiredMessage[num_of_ports] = false;
    }
  }
  // applies requried field checks, and sets required error messages to true
  if (isRequiredField) {
    if (!numPortsProvided) {
      updatedinvalidField[num_of_ports] = true;
      updatedMissingRequiredMessage[num_of_ports] = true;
      updatedCustomErrors[num_of_ports] = false;
      setIncorrectValues((prevArray) => [...prevArray, stationValuesFieldMapping[num_of_ports]]);
      if (!validNumberOfPorts && !updatedMissingRequiredMessage[num_of_ports]) {
        updatedCustomErrors[num_of_ports] = true;
      }
    }
  } else {
    // checks if number of ports is 0 and no ports were listed
    if (
      // @ts-expect-error: Object is possibly 'null'.
      stationValues[port_info].length === 0 &&
      (numPortsProvided === false || String(stationValues[num_of_ports]) === "0")
    ) {
      validNumberOfPorts = true;
      updatedinvalidField[num_of_ports] = false;
      updatedMissingRequiredMessage[num_of_ports] = false;
    }
  }
  // checking for number provided = ports listed for fed funded
  if (!updatedMissingRequiredMessage[num_of_ports]) {
    // checking if provided number is 0, greater than, less than required number and setting custom error message
    if (isRequiredField && String(stationValues[num_of_ports]) === "0") {
      validNumberOfPorts = false;
      updatedCustomErrors[num_of_ports.concat("_zero")] = true;
      // @ts-expect-error: Object is possibly 'null'.
    } else if (stationValues[num_of_ports]! > stationValues[port_info].length) {
      validNumberOfPorts = false;
      updatedCustomErrors[num_of_ports.concat("_greater_than")] = true;
      // @ts-expect-error: Object is possibly 'null'.
    } else if (stationValues[num_of_ports]! < stationValues[port_info].length) {
      validNumberOfPorts = false;
      updatedCustomErrors[num_of_ports.concat("_less_than")] = true;
    }
    // if an invalid port number was entered, we set the invalid field
    if (!validNumberOfPorts && !updatedMissingRequiredMessage[num_of_ports]) {
      updatedinvalidField[num_of_ports] = true;
      setIncorrectValues((prevArray) => [...prevArray, stationValuesFieldMapping[num_of_ports]]);
    }
    // checking if num ports == stations provided to reset invalid field after hitting errors
    if (
      validNumberOfPorts &&
      // @ts-expect-error: Object is possibly 'null'.
      String(stationValues[num_of_ports]) === String(stationValues[port_info].length)
    ) {
      updatedinvalidField[num_of_ports] = false;
    }
  }
  return { updatedCustomErrors, updatedinvalidField, updatedMissingRequiredMessage };
}
