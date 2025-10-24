/**
 * Modal used for importing module data.
 * @packageDocumentation
 **/
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router";

import CryptoJS from "crypto-js";
import Papa from "papaparse";
import { CSVLink } from "react-csv";

import {
  Alert,
  ButtonGroup,
  Button,
  Checkbox,
  ErrorMessage,
  Label,
  Modal,
  ModalHeading,
  ModalFooter,
  Select,
  Spinner,
} from "evchartstorybook";

import { OrganizationSummary } from "../../../interfaces/Organization/organizations-interface";

import { isSRUser } from "../../../utils/authFunctions";
import { FeatureFlagEnum, getFeatureFlagValue, getFeatureFlagList } from "../../../utils/FeatureToggle";
import { getName, getOrgID } from "../../../utils/getJWTInfo";
import {
  PATH_DIRECT_RECIPIENTS,
  PATH_MODULE_IMPORT,
  PATH_MODULE_IMPORT_ERROR_DATA,
  PATH_UPLOAD_OPTIONS,
} from "../../../utils/pathConstants";
import { ROUTE_MODULE_DATA, ROUTE_NETWORK_PROVIDERS, ROUTE_NOT_FOUND } from "../../../utils/routeConstants";

import multiUploadIcon from "../../../assets/MultiUpload_Icon.png";

import "./ImportModal.css";
import "../Modal.css";

/**
 * Interface defining the props that are passed to the ImportModal component
 */
interface ImportModalProps {
  onClose: () => void;
}

/**
 * Interface defining the dropdown selections
 */
interface DropDownProps {
  modules_quarterly: { [key: string]: string };
  modules_other: { [key: string]: string };
  years: string[];
  type: string[];
  quarters: { [key: string]: string };
  direct_recipients?: { [key: string]: string };
}

/**
 * Interface defining the selected info for the module being uploaded
 */
interface ModuleUploadInfo {
  year: string;
  module: string;
  directRecipient: string;
  quarter?: string;
}

/**
 * type defining the module data and metadata being posted
 */
type importAPIHeaders = {
  "Content-Type": string;
  Authorization: string;
  org_id: string;
  parent_org?: string;
  module_id: string;
  quarter?: string;
  year: string;
  uploaded_by: string;
  checksum: string;
};

interface GroupedData {
  [key: string]: any[];
}

/**
 * Initial error state of user selections (all errors assumed to be false)
 */
const initialErrorState = {
  year: false,
  directRecipient: false,
  module: false,
  quarter: false,
  file: false,
};

/**
 * ImportModal
 * @param ImportModalProps
 * @returns the import module modal
 */
export const ImportModal: React.FC<ImportModalProps> = ({ onClose }): React.ReactElement => {
  /**
   * Method for changing the location / route
   */
  const navigate = useNavigate();

  /**
   * Get the api url from the environment variables
   */
  const API_URL = import.meta.env.VITE_API_URL;

  /**
   * Get id and  access token for endpoint authorization
   */
  const access_token = localStorage.getItem("access_token");
  const id_token = localStorage.getItem("id_token");

  /**
   * Feature flag management
   */
  const [presignedUrlFeatureFlag, setPresignedUrlFeatureFlag] = useState(false);

  useEffect(() => {
    getFeatureFlagList().then((results) => {
      setPresignedUrlFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.PresignedUrl));
    });
  }, []);

  /**
   * Multi Upload Components
   */
  const [groupedData, setGroupedData] = useState<GroupedData>({});
  const [multiUploadSelected, setMultiUploadSelected] = useState(false);
  const [isReadyToUpload, setIsReadyToUpload] = useState(false);
  const [invalidRowsCount, setInvalidRowsCount] = useState(0);
  const [dRColumnErrorMessage, setDRColumnErrorMessage] = useState(false);
  const [orgs, setOrgs] = useState<OrganizationSummary[]>([]);

  /**
   * The default / empty selections
   */
  const emptySelections = {
    year: String(new Date().getFullYear()),
    module: "",
    directRecipient: "",
  };

  /**
   * State variables
   */
  const [selectedFile, setSelectedFile] = useState(undefined);
  const [fileSizeError, setFileSizeError] = useState(false);
  const [uploadDisabled, setUploadDisabled] = useState(false);
  const [fileTypeError, setFileTypeError] = useState(false);
  const [unsuccessfulUploadMessage, setUnsuccessfulUploadMessage] = useState(false);
  const [quarterlyModuleSelected, setQuarterlyModuleSelected] = useState(false);
  const [moduleUploadInfo, setModuleUploadInfo] = useState<ModuleUploadInfo>(emptySelections);

  const [formValidity, setFormValidity] = useState<{ [key: string]: boolean }>(initialErrorState);
  const [dropdownOptions, setDropdownOptions] = useState<DropDownProps>();

  /**
   * User and org info
   */
  const [userName, setUserName] = useState<string>("");
  const [orgID, setOrgID] = useState<string>("");
  useEffect(() => {
    const name = getName();
    if (name) {
      setUserName(name);
    }
    const orgID = getOrgID();
    if (orgID) {
      setOrgID(orgID);
    }
  }, []);

  /**
   * State variable for errors in module
   */
  const [numErrors, setNumErrors] = useState(0);
  const [reportGenerated, setReportGenerated] = useState(false);

  /**
   * State variable for the CSV
   */
  const [csvData, setCSVData] = useState("");
  const [moduleName, setModuleName] = useState("");

  /**
   * Event tied to multi upload checkbox selected
   */
  const handleCheckboxChange = () => {
    setMultiUploadSelected((prevChecked) => !prevChecked);
    setFormValidity((prevValidity) => ({
      ...prevValidity,
      directRecipient: false,
    }));
  };

  /**
   * Get the upload options based on user type
   */
  useEffect(() => {
    if (orgID) {
      fetch(`${API_URL}${PATH_UPLOAD_OPTIONS}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `${id_token}`,
        },
      })
        .then((response) => response.json())
        .then((data) => {
          setDropdownOptions(data);
        })
        .catch((err) => {
          console.log(err.message);
        });
    }
  }, [orgID, API_URL, id_token]);

  /**
   * Make an API call here to get the list of DRs for multi upload data validation
   */
  useEffect(() => {
    if (isSRUser()) {
      fetch(`${API_URL}${PATH_DIRECT_RECIPIENTS}`, {
        method: "GET",
        headers: {
          Authorization: `${id_token}`,
        },
      })
        .then((response) => response.json())
        .then((data) => {
          setOrgs(data);
        })
        .catch((err) => {
          console.log(err.message);
        });
    }
  }, [API_URL, id_token]);

  /**
   * Function to check if the dr id in the csv upload actually exists
   * @param dr_id the id to be checked
   * @returns if it exists
   */
  const isDrIdValid = (dr_id: string) => {
    return orgs.some((org) => org.org_friendly_id === dr_id);
  };

  /**
   * Function to return the name of dr from their id
   * @param dr_id the id to be checked
   * @returns the name as a string
   */
  const getOrgNameByDrId = (dr_id: string) => {
    const org = orgs.find((org) => org.org_friendly_id === dr_id);
    return org ? org.name : "Unknown";
  };

  /**
   * Function to go from friendly to uuid for DRs
   * @param friendly_id the friendly id passed in the csv
   * @returns the org uuid
   */
  const getOrgIdByFriendlyId = (friendly_id: string) => {
    const org = orgs.find((org) => org.org_friendly_id === friendly_id);
    return org ? org.org_id : "Invalid";
  };

  /**
   * Parse through the CSV for a multi upload
   */
  const parseCsv = () => {
    if (checkFormValidity() && selectedFile) {
      Papa.parse(selectedFile, {
        header: true,
        complete: (results) => {
          if (!results.meta.fields?.includes("direct_recipient_id")) {
            setDRColumnErrorMessage(true);
            setIsReadyToUpload(false);
          } else {
            setDRColumnErrorMessage(false);
            processCsvData(results.data);
          }
        },
      });
    }
  };

  /**
   * Process the csv and split the data by direct recipients
   * @param data the data from the csv file
   */
  const processCsvData = (data: any[]) => {
    const dataByDrId: GroupedData = {};
    let invalidRows = 0;
    data.forEach((row, index) => {
      const direct_recipient_id = row["direct_recipient_id"];

      const isEmptyRow = Object.values(row).every((value) => value === null || value === undefined || value === "");

      if (isEmptyRow) {
        console.warn(`Row ${index} is empty and will be ignored`);
        return;
      }

      if (
        direct_recipient_id.toString().trim() === "Required" ||
        direct_recipient_id.toString().trim() === "Integer" ||
        (direct_recipient_id.toString().trim() === "" && row["station_id"] === "String(36)") ||
        (direct_recipient_id.toString().trim() === "" && row["station_id"] === "Required")
      ) {
        return; //row contains datatypes or required/ recommended definitions
      }

      if (direct_recipient_id && isDrIdValid(direct_recipient_id)) {
        if (!dataByDrId[direct_recipient_id]) {
          dataByDrId[direct_recipient_id] = [];
        }
        const { direct_recipient_id: removedDrId, ...rest } = row;
        dataByDrId[direct_recipient_id].push(rest);
      } else {
        invalidRows++;
        console.warn(`Row ${index} has invalid or missing direct_recipient_id`, row);
      }
    });

    setGroupedData(dataByDrId);
    setInvalidRowsCount(invalidRows);
    setIsReadyToUpload(true);
    setUploadDisabled(true);
  };

  /**
   * handle uploading for multiple direct recipients
   */
  const uploadMultiDR = async () => {
    setIsReadyToUpload(false);
    for (const direct_recipient_id of Object.keys(groupedData)) {
      const CsvData = Papa.unparse(groupedData[direct_recipient_id]);
      const csvBlob = new Blob([CsvData], { type: "text/csv" });
      const csvFile = new File([csvBlob], `${direct_recipient_id}.csv`, { type: "text/csv" });
      await handleUpload(csvFile, getOrgIdByFriendlyId(direct_recipient_id));
    }
    navigate(ROUTE_MODULE_DATA, {
      state: {
        startTab: "all",
        showUploadAsyncModal: true,
        moduleName:
          dropdownOptions !== undefined && quarterlyModuleSelected === true
            ? dropdownOptions.modules_quarterly[Number(moduleUploadInfo.module)]
            : dropdownOptions !== undefined && dropdownOptions.modules_other[Number(moduleUploadInfo.module)],
        forceRefresh: true,
      },
    });
  };

  /**
   * Event tied to updating the user selections on the modal
   * @param fieldName the field to be updated
   * @param value the value to set it to
   */
  const updateField = (fieldName: string, value: any) => {
    setModuleUploadInfo((prevState: any) => ({
      ...prevState,
      [fieldName]: value,
    }));

    setFormValidity((prevValidity) => ({
      ...prevValidity,
      [fieldName]: false,
    }));

    if (fieldName === "module") {
      checkQuarterlyModuleSelected(value);
    }
  };

  /**
   * Function to check if the module selected is quarterly
   * @param module the module selected
   * @returns if it is a quarterly module
   */
  const checkQuarterlyModuleSelected = (module: string) => {
    if (dropdownOptions && dropdownOptions.modules_quarterly.hasOwnProperty(module)) {
      setQuarterlyModuleSelected(true);
      if (!moduleUploadInfo["quarter"]) {
        moduleUploadInfo["quarter"] = "";
      }
      return true;
    } else {
      setQuarterlyModuleSelected(false);
      delete moduleUploadInfo.quarter;
      setFormValidity((prevValidity) => ({
        ...prevValidity,
        quarter: false,
      }));
      return false;
    }
  };

  /**
   * Function to return classname depending on field validity
   * @param field the field to be checked
   * @returns the appropriate classname
   */
  function inputValid(field: boolean): string {
    if (field) {
      return "usa-input--error";
    } else {
      return "";
    }
  }

  /**
   * Function to check the validity of the selections
   * @returns if the form selections are valid
   */
  const checkFormValidity = () => {
    const updatedFormValidity = { ...formValidity };

    if (moduleUploadInfo.year === "" || moduleUploadInfo.year.indexOf("Select") > -1) {
      updatedFormValidity.year = true;
    }

    if (moduleUploadInfo.module === "" || moduleUploadInfo.module.indexOf("Select") > -1) {
      updatedFormValidity.module = true;
    }

    if (!multiUploadSelected) {
      if (
        dropdownOptions?.direct_recipients !== undefined &&
        (moduleUploadInfo.directRecipient === "" || moduleUploadInfo.directRecipient.indexOf("Select") > -1)
      ) {
        updatedFormValidity.directRecipient = true;
      }
    }

    if (checkQuarterlyModuleSelected(moduleUploadInfo.module)) {
      if (moduleUploadInfo.quarter !== undefined) {
        if (moduleUploadInfo.quarter === "" || moduleUploadInfo.quarter.indexOf("Select") > -1) {
          updatedFormValidity.quarter = true;
        }
      }
    }

    if (selectedFile === undefined) {
      updatedFormValidity.file = true;
    }

    setFormValidity(updatedFormValidity);

    return Object.values(updatedFormValidity).every((valid) => !valid);
  };

  /**
   * Compute the checksum of the file
   * @param targetFile the file that was uploaded
   * @returns the checksum
   */
  const computeChecksum = (targetFile: any): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (event: ProgressEvent<FileReader>) => {
        const arrayBuffer = event.target?.result as ArrayBuffer;
        const wordArray = CryptoJS.lib.WordArray.create(arrayBuffer);
        const hash = CryptoJS.SHA256(wordArray).toString();
        resolve(hash);
      };

      reader.onerror = (error) => reject(error);

      reader.readAsArrayBuffer(targetFile);
    });
  };

  /**
   * Handle a single upload
   */
  const handleSingleUpload = async () => {
    if (checkFormValidity() && selectedFile) {
      let dr_id = "";

      if (moduleUploadInfo.directRecipient) {
        dr_id = moduleUploadInfo.directRecipient;
      }

      Papa.parse<{ [key: string]: string }>(selectedFile, {
        header: true,
        complete: (results) => {
          const filteredData = results.data.map((row) => {
            const { direct_recipient_id: _, ...rest } = row;
            return rest;
          });
          const csvWithoutColumn = Papa.unparse(filteredData);
          const csvBlob = new Blob([csvWithoutColumn], { type: "text/csv" });
          const csvFile = new File([csvBlob], `${dr_id}.csv`, { type: "text/csv" });
          handleUpload(csvFile, dr_id);
        },
      });
    }
  };

  /**
   * Function to post the data
   * @param fileToUpload the file to be uploaded / posted
   * @param drToUpload the dr it is being uploaded for
   */
  const handleUpload = async (fileToUpload: File, drToUpload: string) => {
    if (checkFormValidity()) {
      //set module name for csv download error report
      getModuleNameForErrorReport();

      if (!fileToUpload) return;
      const checksum = await computeChecksum(fileToUpload);
      // Set the headers for the API call
      const importAPIHeaders: importAPIHeaders = {
        "Content-Type": "application/json",
        Authorization: `${access_token}`,
        org_id: orgID, //from jwt
        module_id: moduleUploadInfo.module,
        quarter: "",
        year: moduleUploadInfo.year,
        uploaded_by: userName,
        parent_org: drToUpload,
        checksum: checksum,
      };

      if (moduleUploadInfo.quarter) {
        importAPIHeaders["quarter"] = moduleUploadInfo.quarter;
      }

      if (presignedUrlFeatureFlag) {
        setUploadDisabled(true);
        const presignedUrl = await fetch(`${API_URL}${PATH_MODULE_IMPORT}`, {
          method: "POST",
          headers: importAPIHeaders,
        })
          .then((response) => {
            if (response.ok) {
              return response.json();
            } else {
              throw response;
            }
          })
          .catch((err) => {
            const errorCode = err.status;
            if (errorCode.toString().charAt(0) === "4") {
              //user error
              const errJson = err.json();
              setNumErrors(errJson.error_count);
              fetchErrorData(errJson.upload_id);
            } else if (errorCode.toString().charAt(0) === "5") {
              //server error
              setUnsuccessfulUploadMessage(true);
            }
            setUploadDisabled(false);
          });

        const formData = new FormData();
        for (const [key, value] of Object.entries<string>(presignedUrl["fields"])) formData.append(key, value);

        formData.append("file", fileToUpload);

        fetch(presignedUrl["url"], {
          method: "POST",
          body: formData,
        })
          .then((response) => {
            if (response.ok) {
              // Allow the parent page to be refreshed always on submission of draft
              localStorage.removeItem("beenRefreshed");
              // Refresh the page
              if (!multiUploadSelected) {
                navigate(ROUTE_MODULE_DATA, {
                  state: {
                    startTab: "all",
                    showUploadAsyncModal: true,
                    moduleName:
                      dropdownOptions !== undefined && quarterlyModuleSelected === true
                        ? dropdownOptions.modules_quarterly[Number(moduleUploadInfo.module)]
                        : dropdownOptions !== undefined &&
                          dropdownOptions.modules_other[Number(moduleUploadInfo.module)],
                    forceRefresh: true,
                  },
                });
              }
            } else {
              throw response;
            }
          })
          .catch((err) => {
            setUnsuccessfulUploadMessage(true);
            setUploadDisabled(false);
            console.log(err);
          });
      } else {
        setUploadDisabled(true);
        fetch(`${API_URL}${PATH_MODULE_IMPORT}`, {
          method: "POST",
          headers: importAPIHeaders,
          body: fileToUpload,
        })
          .then((response) => {
            if (response.ok) {
              return response.json();
            } else {
              throw response;
            }
          })
          .then(() => {
            // Allow the parent page to be refreshed always on submission of draft
            localStorage.removeItem("beenRefreshed");
            // Refresh the page
            navigate(ROUTE_MODULE_DATA, {
              state: {
                startTab: "all",
                showUploadAsyncModal: true,
                moduleName:
                  dropdownOptions !== undefined && quarterlyModuleSelected === true
                    ? dropdownOptions.modules_quarterly[Number(moduleUploadInfo.module)]
                    : dropdownOptions !== undefined && dropdownOptions.modules_other[Number(moduleUploadInfo.module)],
                forceRefresh: true,
              },
            });
          })
          .catch(async (err) => {
            const errorCode = err.status;
            console.log(errorCode);
          });
      }
    }
  };

  /**
   * Get the module name for the error report download
   */
  const getModuleNameForErrorReport = () => {
    if (dropdownOptions !== undefined) {
      if (quarterlyModuleSelected === true) {
        setModuleName(dropdownOptions.modules_quarterly[Number(moduleUploadInfo.module)]);
      } else {
        setModuleName(dropdownOptions.modules_other[Number(moduleUploadInfo.module)]);
      }
    }
  };

  /**
   * resetting error variables for a new module upload
   */
  const newUpload = () => {
    setNumErrors(0);
    setUnsuccessfulUploadMessage(false);
    setFileSizeError(false);
    setFileTypeError(false);
    setIsReadyToUpload(false);
    setUploadDisabled(false);
    setModuleUploadInfo(emptySelections);
    setMultiUploadSelected(false);
    setCSVData("");
    setModuleName("");
  };

  /**
   * Function to get the error info for a failed upload
   * @param uploadId the id of the uploaded data
   */
  const fetchErrorData = (uploadId: any) => {
    fetch(`${API_URL}${PATH_MODULE_IMPORT_ERROR_DATA}?upload_id=${uploadId}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `${access_token}`,
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
        setCSVData(data);
        setReportGenerated(true);
      })
      .catch((err) => {
        const errorCode = err.status;
        if (errorCode === 400) {
          navigate(ROUTE_NOT_FOUND);
        }
      });
  };

  /**
   * Handle the change for a file upload
   * @param e the file event
   */
  const handleChange = (e: any) => {
    if (e.target.files[0] !== undefined) {
      setFormValidity((prevValidity) => ({
        ...prevValidity,
        file: false,
      }));

      setFileSizeError(false);
      setFileTypeError(false);

      const fileSizeError = e.target.files[0].size > 10 * 1024 * 1024;
      const fileTypeError = !e.target.files[0].name.toLowerCase().endsWith(".csv");

      if (fileSizeError || fileTypeError) {
        if (fileSizeError) {
          setFileSizeError(true);
        }
        if (fileTypeError) {
          setFileTypeError(true);
        }
      } else {
        setDRColumnErrorMessage(false);
        setFileSizeError(false);
        setFileTypeError(false);
        setSelectedFile(e.target.files[0]);
      }
    } else {
      setSelectedFile(undefined);
    }
  };

  return (
    <div className="ImportModal">
      <Modal onClose={onClose} forceAction={true}>
        <ModalHeading id="modal-2-heading" className="bottom-border">
          Upload Module Data
        </ModalHeading>

        {isReadyToUpload && (
          <div>
            {invalidRowsCount === 0 ? (
              <div className="multi-upload-icon">
                <img
                  id="multiUploadIcon"
                  className="multi-upload-icon"
                  src={multiUploadIcon}
                  alt="Mutli Upload Icon"
                  title="Mutli Upload Icon"
                />
                <h3>Your data will be split into separate drafts for each identified direct recipient.</h3>
              </div>
            ) : (
              <>
                <h3>We found errors in your data upload.</h3>
                <Alert type="error" headingLevel="h4" className="invalid-rows-count-alert">
                  {invalidRowsCount} rows in your file cannot be linked to valid unique direct recipient IDs.
                </Alert>
              </>
            )}

            <div className="flex-box multi-dr-list-header">
              <span>
                {" "}
                {moduleUploadInfo.module === "2" || moduleUploadInfo.module === "3" || moduleUploadInfo.module === "4"
                  ? dropdownOptions?.modules_quarterly[moduleUploadInfo.module]
                  : dropdownOptions?.modules_other[moduleUploadInfo.module]}{" "}
              </span>
              <span>
                {" "}
                {moduleUploadInfo.year}{" "}
                {moduleUploadInfo.quarter ? dropdownOptions?.quarters[moduleUploadInfo.quarter] : ""}
              </span>
            </div>

            <div className="scrollable-container">
              {invalidRowsCount > 0 && (
                <ErrorMessage className="dr-error-message">
                  <div className="flex-box multi-dr-list">
                    <span> Direct Recipient ID Error </span>
                    <span> {invalidRowsCount} rows </span>
                  </div>{" "}
                </ErrorMessage>
              )}

              {Object.keys(groupedData).map((dr_id) => (
                <div className="flex-box multi-dr-list" key={dr_id}>
                  <span> {getOrgNameByDrId(dr_id)} </span>
                  <span>
                    {" "}
                    {groupedData[dr_id].length} {groupedData[dr_id].length > 1 ? "rows" : "row"}{" "}
                  </span>
                </div>
              ))}
            </div>

            {invalidRowsCount > 0 && (
              <>
                <div className="multi-error-correction-guidance">
                  <p>
                    {" "}
                    <b> To correct error</b>
                  </p>
                  <ol className="guidance-ol">
                    <li className="multi-error-li">
                      {" "}
                      Go to <b>Resources </b>
                      {">"}{" "}
                      <a className="evchart-link-bold" href={ROUTE_NETWORK_PROVIDERS}>
                        {" "}
                        Direct Recipient IDs
                      </a>
                    </li>
                    <li className="multi-error-li">
                      Identify and replace incorrect Direct Recipient ID values used in data upload, then retry upload
                    </li>
                  </ol>
                </div>
                <div>
                  This file will be discarded from EV-ChART. Once you have corrected the errors in the file, you can
                  upload it again for submission.
                </div>
              </>
            )}

            <ModalFooter>
              <ButtonGroup className="modal-button-group">
                {invalidRowsCount > 0 ? (
                  <Button type="button" onClick={newUpload}>
                    Upload New Data
                  </Button>
                ) : (
                  <Button type="button" onClick={uploadMultiDR}>
                    Confirm Upload
                  </Button>
                )}
                <Button onClick={onClose} type="button" unstyled className="padding-105 text-center">
                  Cancel
                </Button>
              </ButtonGroup>
            </ModalFooter>
          </div>
        )}

        {numErrors > 0 && (
          <div style={{ marginTop: 15 }}>
            <div id="errorText">
              <p>We found errors in your data upload.</p>
            </div>
            <Alert type="error" headingLevel="h3">
              {numErrors} rows in your file have errors
            </Alert>
            <div id="downloadErrorText">
              <p>Download the Error Report (CSV) to view the full detailed list of errors.</p>
            </div>
            {reportGenerated ? (
              <>
                <ButtonGroup>
                  {csvData.length > 0 && (
                    <CSVLink
                      id="csvDownloadButton"
                      type="button"
                      className="downloadErrorReportButton"
                      data={csvData}
                      filename={"Error_Log_" + moduleName + ".csv"}
                    >
                      Download Error Report (CSV)
                    </CSVLink>
                  )}
                </ButtonGroup>
              </>
            ) : (
              <>
                <div className="spinner-container">
                  <div className="spinner-content">
                    <Spinner></Spinner>
                  </div>
                </div>
              </>
            )}

            <div id="downloadErrorText">
              <p>
                This file will be discarded from EV-ChART. Once you have corrected the errors in the file, you can
                upload it again for submission.
              </p>
            </div>

            {reportGenerated && (
              <ModalFooter>
                <ButtonGroup className="modal-button-group">
                  <Button onClick={newUpload} type="button" className="padding-105 text-center">
                    Upload New Data
                  </Button>
                  <Button onClick={onClose} type="button" unstyled className="padding-105 text-center">
                    Close
                  </Button>
                </ButtonGroup>
              </ModalFooter>
            )}
          </div>
        )}

        {!uploadDisabled && (
          <>
            <div style={{ marginTop: 15 }}>
              <div>
                Use the{" "}
                <a
                  className="evchart-link"
                  href="https://driveelectric.gov/files/ev-chart-data-input-template.xlsx"
                  target="_blank"
                  rel="noreferrer"
                >
                  EV-ChART Data Input Template
                </a>{" "}
                and the{" "}
                <a
                  className="evchart-link"
                  href="https://driveelectric.gov/files/ev-chart-data-guidance.pdf"
                  target="_blank"
                  rel="noreferrer"
                >
                  EV-ChART Data Format and Preparation Guidance
                </a>{" "}
                to support your upload.
              </div>
              {dropdownOptions && (
                <div className="dropdown-options">
                  {isSRUser() && (
                    <div className="multi-upload-checkbox">
                      <Checkbox
                        id="multiUploadCheckbox"
                        name="checkbox"
                        label="This file contains data for multiple direct recipients"
                        onChange={handleCheckboxChange}
                      />
                    </div>
                  )}
                  {dropdownOptions?.direct_recipients !== undefined && (
                    <div className="upload-modal-selection">
                      <Label htmlFor="input-year" className="required-field">
                        Direct Recipient
                      </Label>
                      <Select
                        id="input-select"
                        name="input-select"
                        className={inputValid(formValidity.directRecipient)}
                        onChange={(e) => updateField("directRecipient", e.target.value)}
                        disabled={multiUploadSelected}
                      >
                        <option> - Select - </option>
                        {dropdownOptions?.direct_recipients &&
                          Object.entries(dropdownOptions.direct_recipients).map(([key, value]) => (
                            <option key={key} value={key}>
                              {value}
                            </option>
                          ))}
                      </Select>
                      {formValidity.directRecipient && <ErrorMessage>This field is required.</ErrorMessage>}
                    </div>
                  )}

                  <div className="upload-modal-selection">
                    <Label htmlFor="input-year" className="required-field">
                      Reporting Year
                    </Label>
                    <Select
                      id="input-select"
                      name="input-select"
                      className={inputValid(formValidity.year)}
                      value={moduleUploadInfo.year}
                      onChange={(e) => updateField("year", e.target.value)}
                    >
                      <option> - Select - </option>
                      {dropdownOptions?.years.map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </Select>
                    {formValidity.year && <ErrorMessage>This field is required.</ErrorMessage>}
                  </div>

                  <div className="upload-modal-selection">
                    <Label htmlFor="input-module" className="required-field">
                      Module
                    </Label>
                    <Select
                      id="input-select"
                      name="input-select"
                      className={inputValid(formValidity.module)}
                      onChange={(e) => updateField("module", e.target.value)}
                    >
                      <option> - Select - </option>
                      {Object.entries(dropdownOptions.modules_quarterly).map(([key, value]) => (
                        <option key={key} value={key}>
                          {value}
                        </option>
                      ))}
                      {Object.entries(dropdownOptions.modules_other).map(([key, value]) => (
                        <option key={key} value={key}>
                          {value}
                        </option>
                      ))}
                    </Select>
                    {formValidity.module && <ErrorMessage>This field is required.</ErrorMessage>}
                  </div>
                  {quarterlyModuleSelected && (
                    <div className="upload-modal-selection">
                      <Label htmlFor="input-quarter" className="required-field">
                        Quarter
                      </Label>
                      <Select
                        id="input-select"
                        name="input-select"
                        className={inputValid(formValidity.quarter)}
                        onChange={(e) => updateField("quarter", e.target.value)}
                      >
                        <option> - Select - </option>
                        {Object.entries(dropdownOptions.quarters).map(([key, value]) => (
                          <option key={key} value={key}>
                            {value}
                          </option>
                        ))}
                      </Select>
                      {formValidity.quarter && <ErrorMessage>This field is required.</ErrorMessage>}
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="file-selection-container">
              <Label htmlFor="file">
                {" "}
                Upload a CSV file by clicking the button below and selecting a single file. The file size limit is 10
                MB.
              </Label>
              <form>
                <input type="file" accept="csv" onChange={handleChange} />
              </form>
              {formValidity.file && <ErrorMessage> Please select a file. </ErrorMessage>}
            </div>

            {fileSizeError && <ErrorMessage> Please upload a file less than 10 MB. </ErrorMessage>}
            {fileTypeError && <ErrorMessage> Please upload a file with the CSV extension. </ErrorMessage>}
            {unsuccessfulUploadMessage && <ErrorMessage> Upload was unsuccessful. Please try again. </ErrorMessage>}
            {dRColumnErrorMessage && (
              <ErrorMessage>
                {" "}
                Please upload a file with a column titled "direct_recipient_id" <br />
                Go to Resources {">"} <a href={ROUTE_NETWORK_PROVIDERS}> Direct Recipient IDs </a> for support.{" "}
              </ErrorMessage>
            )}

            <ModalFooter>
              <ButtonGroup className="modal-button-group">
                {multiUploadSelected ? (
                  <Button type="button" onClick={parseCsv}>
                    Upload
                  </Button>
                ) : (
                  <Button type="button" onClick={handleSingleUpload} disabled={uploadDisabled}>
                    Upload
                  </Button>
                )}
                <Button onClick={onClose} type="button" unstyled className="padding-105 text-center">
                  Cancel
                </Button>
              </ButtonGroup>
            </ModalFooter>
          </>
        )}

        {uploadDisabled && !isReadyToUpload && (
          <>
            <div className="spinner-container">
              <div className="spinner-content">
                <Spinner></Spinner>
              </div>
              <div id="uploadText">
                <p>Uploading the file.</p>
              </div>
              <div id="timingText">
                <p>This may take a few minutes. Keep this window open until the upload is complete.</p>
              </div>
            </div>
          </>
        )}
      </Modal>
    </div>
  );
};

export default ImportModal;
