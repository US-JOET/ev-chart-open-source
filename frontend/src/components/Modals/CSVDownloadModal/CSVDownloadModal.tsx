/**
 * CSV download modal for module data.
 * @packageDocumentation
 **/
import { useEffect, useState } from "react";
import { useNavigate } from "react-router";

import { CSVLink } from "react-csv";

import { Button, ButtonGroup, Modal, ModalHeading, ModalFooter, Spinner } from "evchartstorybook";

import { FeatureFlagEnum, getFeatureFlagValue, getFeatureFlagList } from "../../../utils/FeatureToggle";
import { PATH_MODULE_DATA, PATH_MODULE_DOWNLOAD, PATH_MODULE_IMPORT_ERROR_DATA } from "../../../utils/pathConstants";
import { ROUTE_NOT_AUTHORIZED } from "../../../utils/routeConstants";

import "./CSVDownloadModal.css";
import "../Modal.css";

/**
 * type defining the props that are passed to the CSVDownloadModal component
 */
type CSVDownloadModalProps = {
  apiPath: string;
  moduleNum?: string;
  moduleName?: string;
  uploadId?: string;
  queryParams?: string;
  handleShowAlert?: () => void;
  handleHideAlert?: () => void;
  onClose: () => void;
};

/**
 * CSVDownloadModal
 * @param CSVDownloadModalProps information about the module being downloaded
 * @returns the download modal
 */
export const CSVDownloadModal: React.FC<CSVDownloadModalProps> = ({
  apiPath,
  uploadId,
  moduleNum,
  moduleName,
  queryParams,
  handleShowAlert,
  handleHideAlert,
  onClose,
}): React.ReactElement => {
  /**
   * Method for changing the location / route
   */
  const navigate = useNavigate();

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
   * Get the api url from the environment variables
   */
  const API_URL = import.meta.env.VITE_API_URL;

  /**
   * Get id and access token for endpoint authorization
   */
  const access_token = localStorage.getItem("access_token");
  const id_token = localStorage.getItem("id_token");

  /**
   * State variable for the CSV
   */
  const [csvData, setCSVData] = useState(undefined);
  const [fileName, setFileName] = useState<string>("");

  /**
   * close the modal after download is complete
   */
  const handleCloseModalAfterDownload = () => {
    onClose();
    if (handleHideAlert !== undefined) {
      handleHideAlert();
    }
  };

  /**
   * Fetch the module data
   */
  useEffect(() => {
    let headersAPI: any;
    let parsedAPIPath: string = "";
    let appropriateToken: string | null = id_token;

    if (apiPath === "data") {
      setFileName(uploadId + "_data.csv");
      headersAPI = {
        upload_id: uploadId,
        download: true,
      };
      parsedAPIPath = PATH_MODULE_DATA;
    } else if (apiPath === "download") {
      setFileName("module_" + moduleNum + "_data.csv");
      parsedAPIPath = `${PATH_MODULE_DOWNLOAD}?${queryParams}`;
    } else if (apiPath === "import-error-data") {
      //setting the file name for the error report
      const unformattedFileName = "Error_Report_" + moduleName + ".csv";
      const formattedFileName = unformattedFileName.replace(/ /g, "_").replace(/:/g, "");
      setFileName(formattedFileName);

      parsedAPIPath = `${PATH_MODULE_IMPORT_ERROR_DATA}?upload_id=${uploadId}`;
      appropriateToken = access_token;
    }

    fetch(`${API_URL}${parsedAPIPath}`, {
      method: "GET",
      headers: { ...headersAPI, Authorization: `${appropriateToken}` },
    })
      .then((response) => {
        if (response.ok) {
          return response.json();
        } else {
          throw response;
        }
      })
      .then((data) => {
        if (data.is_data_present === false) {
          onClose();
          if (handleShowAlert !== undefined) {
            handleShowAlert();
          }
        } else if (presignedUrlFeatureFlag) {
          setCSVData(data.url);
        } else {
          setCSVData(data.data);
        }
      })
      .catch((err) => {
        const errorCode = err.status;
        if (errorCode === 403) {
          navigate(ROUTE_NOT_AUTHORIZED);
        }
      });
  }, [presignedUrlFeatureFlag, apiPath]);

  return (
    <div className="csv-download-modal">
      <Modal onClose={onClose} aria-labelledby="csv-modal-heading" aria-describedby="csv-modal-description">
        <ModalHeading id="csvModalHeading" className="bottom-border">
          {apiPath === "import-error-data" ? "Download Error Report as CSV" : "Download as CSV"}
        </ModalHeading>
        {csvData ? (
          <>
            <div className="modal-body">
              <p>
                View the full{" "}
                <a
                  href="https://driveelectric.gov/evchart-terms"
                  target="_blank"
                  className="evchart-link-reference"
                  rel="noreferrer"
                >
                  EV-ChART Terms of Use
                </a>
                .
              </p>
            </div>
            <ModalFooter id="csvModalFooter">
              <ButtonGroup>
                {presignedUrlFeatureFlag ? (
                  <>
                    <a
                      className="usa-button"
                      target="_blank"
                      rel="noopener noreferrer"
                      href={csvData}
                      download={fileName}
                      onClick={handleCloseModalAfterDownload}
                    >
                      Download
                    </a>
                  </>
                ) : (
                  <>
                    <CSVLink
                      id="csvDownloadButton"
                      className="usa-button"
                      data={csvData}
                      filename={fileName}
                      onClick={handleCloseModalAfterDownload}
                    >
                      Download
                    </CSVLink>
                  </>
                )}
                <Button onClick={onClose} type="button" unstyled className="padding-105 text-center">
                  Cancel
                </Button>
              </ButtonGroup>
            </ModalFooter>
          </>
        ) : (
          <>
            <div className="spinner-modal-body">
              <Spinner></Spinner>
            </div>
          </>
        )}
      </Modal>
    </div>
  );
};

export default CSVDownloadModal;
