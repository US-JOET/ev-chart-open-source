/**
 * Query and download functionality.
 * @packageDocumentation
 **/
import React, { createRef, useState, useEffect } from "react";

import {
  Breadcrumb,
  BreadcrumbBar,
  BreadcrumbLink,
  Button,
  ButtonGroup,
  Chip,
  ComboBox,
  GridContainer,
  Grid,
  Radio,
  Select,
  ComboBoxRef,
  Alert,
  Tooltip,
  Icon,
  Label,
} from "evchartstorybook";

import { OrganizationSummary, NetworkProviderInfo } from "../../interfaces/Organization/organizations-interface";
import { StationOption } from "../../interfaces/Stations/stations-interface";
import { OptionsList } from "../../interfaces/ui-components-interfaces";

import { isDRUser } from "../../utils/authFunctions";
import { getOrgID } from "../../utils/getJWTInfo";
import {
  PATH_DIRECT_RECIPIENTS,
  PATH_NETWORK_PROVIDERS,
  PATH_REPORTING_YEARS,
  PATH_STATION_ORG_ID,
  PATH_SUB_RECIPIENTS,
} from "../../utils/pathConstants";
import { ROUTE_HOME } from "../../utils/routeConstants";
import { FeatureFlagEnum, getFeatureFlagValue, getFeatureFlagList } from "../../utils/FeatureToggle";


import CSVDownloadModal from "../../components/Modals/CSVDownloadModal/CSVDownloadModal";

import "./QueryDownload.css";
import CustomLink from "../../components/Tooltip/tooltips";

function QueryDownload() {
  /**
   * Get the api and base url from the environment variables
   */
  const API_URL = import.meta.env.VITE_API_URL;
  const BASE_URL = import.meta.env.VITE_PUBLIC_URL;

  /**
   * Get access and id token for endpoint authorization
   */
  const id_token = localStorage.getItem("id_token");

  const [cadenceSelection, setCadenceSelection] = useState<string>("");

  const [selectedRadioButton, setSelectedRadioButton] = useState<number>(0);
  const [oneTimeModuleSelected, setOneTimeModuleSelected] = useState<boolean>(false);

  const [reportingYearSelections, setReportingYearSelections] = useState<string[]>([]);
  const [quartersSelections, setQuartersSelections] = useState<string[]>([]);
  const [federalFundingStatusSelections, setfederalFundingStatusSelections] = useState<string[]>([]);
  const [networkProviderSelections, setNetworkProviderSelections] = useState<string[]>([]);;
  const [subrecipientSelections, setSubrecipientSelections] = useState<string[]>([]);
  const [directRecipientSelections, setDirectRecipientSelections] = useState<string[]>([]);
  const [stationsSelections, setStationsSelections] = useState<string[]>([]);

  const [networkProviderOptions, setNetworkProviderOptions] = useState<NetworkProviderInfo[]>([]);
  const [availableReportingYears, setAvailableReportingYears] = useState<{ year: string }[]>([]);

  const [openDownloadModal, setOpenDownloadModal] = useState(false);
  const [queryParams, setQueryParams] = useState<string>("");

  const [showNoDataAlert, setShowNoDataAlert] = useState(false);

  /**
   * Feature flag management
   * Toggles:
   *  * Check if we have the ability to register non fed funded stations
   */
  const [RegisterNonFedFundedStationFeatureFlag, setRegisterNonFedFundedStationFeatureFlag] = useState(false);
  const [QueryDownloadRefactorFeatureFlag, setQueryDownloadRefactorFeatureFlag] = useState(false);
  useEffect(() => {
    getFeatureFlagList().then((results) => {
      setRegisterNonFedFundedStationFeatureFlag(
        getFeatureFlagValue(results, FeatureFlagEnum.RegisterNonFedFundedStation),
      );
      setQueryDownloadRefactorFeatureFlag(
        getFeatureFlagValue(results, FeatureFlagEnum.QueryDownloadRefactor),
      );
    });
  }, []);

  /**
   * References created to each combobox
   */
  const refReportingYearComboBox = createRef<ComboBoxRef>();
  const refQuartersComboBox = createRef<ComboBoxRef>();
  const refNetworkProviderComboBox = createRef<ComboBoxRef>();
  const refSubrecipientComboBox = createRef<ComboBoxRef>();
  const refDirectRecipientComboBox = createRef<ComboBoxRef>();
  const refStationsComboBox = createRef<ComboBoxRef>();
  const refFederalFundingStatusComboBox = createRef<ComboBoxRef>();

  const checkOneTimeSelection = (id: number) => {
    const oneTimeModule = [1, 6, 8, 9].includes(id);
    setOneTimeModuleSelected(oneTimeModule);
    if (oneTimeModule) {
      setReportingYearSelections([]);
    }
  };

  const handleRadioButtonChange = (id: number) => {
    setShowNoDataAlert(false);
    setSelectedRadioButton((prevSelected) => {
      if (prevSelected === id) {
        setOneTimeModuleSelected(false);
        return 0;
      } else {
        checkOneTimeSelection(id);
        return id;
      }
    });
  };

  const handleYearChange = (value: any) => {
    if (value) {
      setShowNoDataAlert(false);
      setReportingYearSelections((prevSelected) => {
        if (prevSelected.includes(value)) {
          return prevSelected.filter((radioButtonId) => radioButtonId !== value);
        } else {
          return [...prevSelected, value];
        }
      });
    }
    refReportingYearComboBox.current?.clearSelection();
  };

  const handleQuarterChange = (value: any) => {
    if (value) {
      setShowNoDataAlert(false);
      setQuartersSelections((prevSelected) => {
        if (prevSelected.includes(value)) {
          return prevSelected.filter((radioButtonId) => radioButtonId !== value);
        } else {
          return [...prevSelected, value];
        }
      });
    }
    refQuartersComboBox.current?.clearSelection();
  };

  const handleNetworkProviderChange = (value: any) => {
    if (value){
      if(QueryDownloadRefactorFeatureFlag){
          const uuid = networkProviderOptions.find((item) => item.network_provider_value === value)!.network_provider_uuid
          setShowNoDataAlert(false);
          setNetworkProviderSelections((prevSelected) => {
            if (prevSelected.includes(uuid)) {
              return prevSelected.filter((radioButtonId) => radioButtonId !== uuid);
            } else {
              return [...prevSelected, uuid];
            }
          });
      } else {
        setShowNoDataAlert(false);
        setNetworkProviderSelections((prevSelected) => {
          if (prevSelected.includes(value)) {
            return prevSelected.filter((radioButtonId) => radioButtonId !== value);
          } else {
            return [...prevSelected, value];
          }
        });
      }
    }
    refNetworkProviderComboBox.current?.clearSelection();
  };

  const handleFederalFundingStatusChange = (value: any) => {
    if (value) {
      setShowNoDataAlert(false);
      setfederalFundingStatusSelections((prevSelected) => {
        if (prevSelected.includes(value)) {
          return prevSelected.filter((radioButtonId) => radioButtonId !== value);
        } else {
          return [...prevSelected, value];
        }
      });
    }
    refFederalFundingStatusComboBox.current?.clearSelection();
  };


  const handleSubrecipientChange = (value: any) => {
    if (value) {
      setShowNoDataAlert(false);
      setSubrecipientSelections((prevSelected) => {
        if (prevSelected.includes(value)) {
          return prevSelected.filter((radioButtonId) => radioButtonId !== value);
        } else {
          return [...prevSelected, value];
        }
      });
    }
    refSubrecipientComboBox.current?.clearSelection();
  };

  const handleDirectRecipientChange = (value: any) => {
    if (value) {
      setShowNoDataAlert(false);
      setDirectRecipientSelections((prevSelected) => {
        if (prevSelected.includes(value)) {
          return prevSelected.filter((radioButtonId) => radioButtonId !== value);
        } else {
          return [...prevSelected, value];
        }
      });
    }
    refDirectRecipientComboBox.current?.clearSelection();
  };

  const handleStationChange = (value: any) => {
    if (value) {
      setShowNoDataAlert(false);
      setStationsSelections((prevSelected) => {
        if (prevSelected.includes(value)) {
          return prevSelected.filter((radioButtonId) => radioButtonId !== value);
        } else {
          return [...prevSelected, value];
        }
      });
    }
    refStationsComboBox.current?.clearSelection();
  };

  const handleCadenceSelection = (value: any) => {
    setShowNoDataAlert(false);
    setCadenceSelection(value);
    handleClearFilters();
  };

  const handleOpenDownloadData = () => {
    setOpenDownloadModal(true);
    getQueryParams();
  };

  const handleCloseDownloadData = () => {
    setOpenDownloadModal(false);
  };

  const handleShowAlert = () => {
    setShowNoDataAlert(true);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleHideAlert = () => {
    setShowNoDataAlert(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  /**
   * Clear all the filters
   */
  const handleClearFilters = () => {
    setSelectedRadioButton(0);
    setReportingYearSelections([]);
    setQuartersSelections([]);
    setNetworkProviderSelections([]);
    setSubrecipientSelections([]);
    setDirectRecipientSelections([]);
    setStationsSelections([]);
    setShowNoDataAlert(false);

    refReportingYearComboBox.current?.clearSelection();
    refQuartersComboBox.current?.clearSelection();
    refNetworkProviderComboBox.current?.clearSelection();
    refSubrecipientComboBox.current?.clearSelection();
    refDirectRecipientComboBox.current?.clearSelection();
    refStationsComboBox.current?.clearSelection();
  };

  const DefaultBreadcrumb = (): React.ReactElement => (
    <BreadcrumbBar>
      <Breadcrumb>
        <BreadcrumbLink href={`${BASE_URL}${ROUTE_HOME}`}>
          <span>Home</span>
        </BreadcrumbLink>
      </Breadcrumb>
      <Breadcrumb current>
        <span>Download Module Data</span>
      </Breadcrumb>
    </BreadcrumbBar>
  );


  /**
   * Reporting cadence numbers to their labels
   */
  const reportingCadence: { key: string; label: string }[] = [
    { key: "one_time_annual", label: "One-Time and Annual"},
    { key: "quarterly", label: "Quarterly"}
  ];

  /**
   * One time modules numbers to their labels
   */
  const oneTimeModules: { key: number; label: string }[] = [
    { key: 1, label: "Module 1: Station Location" },
    { key: 6, label: "Module 6: Station Operator Identity" },
    { key: 8, label: "Module 8: DER Information" },
    { key: 9, label: "Module 9: Capital and Installation Costs" },
  ];

  /**
   * Annual modules numbers to their labels
   */
  const annualModules: { key: number; label: string }[] = [
    { key: 5, label: "Module 5: Maintenance Costs" },
    { key: 7, label: "Module 7: Station Operator Program" },
  ];

  /**
   * Quarterly modules numbers to their labels
   */
  const quarterlyModules: { key: number; label: string }[] = [
    { key: 2, label: "Module 2: Charging Sessions" },
    { key: 3, label: "Module 3: Uptime" },
    { key: 4, label: "Module 4: Outages" },
  ];

  /**
   * Create the query params based on user selections
   */
  const getQueryParams = async () => {
    const params = new URLSearchParams();
    // need moudles to be passed in the same structure as other fields ex: "modules":'["2"]'
    params.append("modules", JSON.stringify([selectedRadioButton.toString()]));

    if (reportingYearSelections && reportingYearSelections.length > 0) {
      params.append("years", JSON.stringify(reportingYearSelections));
    }
    if (quartersSelections && quartersSelections.length > 0) {
      params.append("quarters", JSON.stringify(quartersSelections));
    }
    // passing in -1 if a quarterly module is selected but user wants to select all quarters
    else if (selectedRadioButton === 2 || selectedRadioButton === 3 || selectedRadioButton === 4) {
      params.append("quarters", JSON.stringify(["-1"]));
    }
    if (networkProviderSelections && networkProviderSelections.length > 0) {
      params.append("network_providers", JSON.stringify(networkProviderSelections));
    }
    if (RegisterNonFedFundedStationFeatureFlag === true && federalFundingStatusSelections && federalFundingStatusSelections.length > 0) {
      params.append("federal_funding_status", JSON.stringify(federalFundingStatusSelections));
    }
    // for dr query download
    if (isDRUser() && directRecipientSelections.length < 1) {
      directRecipientSelections.push(getOrgID());
    }
    // for dr query download
    if (isDRUser() && directRecipientSelections.length < 1) {
      directRecipientSelections.push(getOrgID());
    }
    if (directRecipientSelections && directRecipientSelections.length > 0) {
      params.append("drs", JSON.stringify(directRecipientSelections));
    }
    if (subrecipientSelections && subrecipientSelections.length > 0) {
      params.append("srs", JSON.stringify(subrecipientSelections));
    }
    if (stationsSelections && stationsSelections.length > 0) {
      params.append("stations", JSON.stringify(stationsSelections));
    }
    setQueryParams(params.toString());
  };

  useEffect(() => {
    fetch(`${API_URL}${PATH_SUB_RECIPIENTS}`, {
      method: "GET",
      headers: {
        Authorization: `${id_token}`,
        only_authorized: "True",
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

  useEffect(() => {
    fetch(`${API_URL}${PATH_REPORTING_YEARS}`, {
      method: "GET",
      headers: {
        Authorization: `${id_token}`,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        setAvailableReportingYears(data);
      })
      .catch((err) => {
        console.log(err.message);
      });
  }, []);

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

  useEffect(() => {
    if (!isDRUser()) {
      fetch(`${API_URL}${PATH_DIRECT_RECIPIENTS}`, {
        method: "GET",
        headers: {
          Authorization: `${id_token}`,
        },
      })
        .then((response) => response.json())
        .then((data) => {
          setDirectRecipientOptions(data);
        })
        .catch((err) => {
          console.log(err.message);
        });
    }
  }, []);

  /**
   * Get the station ids of federal or non_federally funded stations.
   * Will only return the station ids that is specified in the "Federal Funding Status" combo box filter
   * When the filter is udpated, the selected stations are also updated dynamically
   */
  useEffect(() => {
    // updates path parameters depending on federal or non federally funded filter selection
    let pathParameters="status=Active"

    // update pathParameter if default is selected or both funding options are selected
    if (RegisterNonFedFundedStationFeatureFlag === true && (federalFundingStatusSelections.length === 0 || federalFundingStatusSelections.length === 2)){
      pathParameters="status=Active"
    }
    // update pathParameter if only querying for fed funded stations
    else if (RegisterNonFedFundedStationFeatureFlag === true && federalFundingStatusSelections.includes('1')){
      pathParameters += "&federal_funding_status=fed_funded"
    }
    // update pathParameter if only querying for non-fed funded stations
    else if (RegisterNonFedFundedStationFeatureFlag === true && federalFundingStatusSelections.includes('0')){
      pathParameters += "&federal_funding_status=non_fed_funded"
    }

    fetch(`${API_URL}${PATH_STATION_ORG_ID}?${pathParameters}`, {
      method: "GET",
      headers: {
        Authorization: `${id_token}`,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        setStationOptions(data);

        // Removing any selected stations not in the new stations options
        setStationsSelections((prevSelected) =>
          prevSelected.filter((selectedUuid) =>
              data.some((item: StationOption ) => item.station_uuid === selectedUuid)
          ));
        })
      .catch((err) => {
        console.log(err.message);
      });
  }, [federalFundingStatusSelections]);

  const quarterlyCadenceList: OptionsList[] = [
    {
      value: "1",
      label: "Quarter 1",
    },
    {
      value: "2",
      label: "Quarter 2",
    },
    {
      value: "3",
      label: "Quarter 3",
    },
    {
      value: "4",
      label: "Quarter 4",
    },
  ];

  const federalFundingStatusList: OptionsList[] = [
    {
      value: "1",
      label: "Federally Funded Stations",
    },
    {
      value: "0",
      label: "Non-Federally Funded Stations",
    },
  ];

  /**
   * The options returned from the /org/subrecipients endpoint
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
  const directRecipientList = directRecipientOptions?.map(
    (item: { org_id: string; name: string; org_friendly_id: string }) => ({
      value: item.org_id,
      label: `${item.name} - ${item.org_friendly_id}`,
    }),
  );

  /**
   * The options returned from the stations endpoint for use in the combobox
   */
  const [stationOptions, setStationOptions] = useState<StationOption[]>([
    {
      station_uuid: "",
      station_id: "",
      nickname: "",
    },
  ]);

  /**
   * The stations options converted to a list for use within the combobox component
   */
  const stationsList: OptionsList[] = stationOptions?.map(
    (item: { station_uuid: string; station_id: string; nickname: string }) => ({
      value: item.station_uuid,
      label: `${item.nickname} - ${item.station_id}`,
    }),
  );

  const networkProvidersList: OptionsList[] = networkProviderOptions?.map(
    (item : {network_provider_uuid: string; network_provider_value: string; description:string;}) => ({
      value: item.network_provider_value,
      label: item.description
  }));

  const yearsList: OptionsList[] = availableReportingYears.map(({ year }) => ({
    value: year,
    label: year,
  }));


  /**
   * Returns the label from the id
   * @param id the id being searched
   * @param options the available options
   * @returns the label if found
   */
  const getLabelFromId = (id: string, options: OptionsList[]): string | undefined => {
    const foundOption = options.find((option) => option.value === id);
    return foundOption ? foundOption.label : undefined;
  };

  return (
    <div className="queryAndDownload">
      <div>
        <GridContainer>
          <DefaultBreadcrumb />
        </GridContainer>
      </div>
      <div id="QueryAndDownload">
        <div className="usa-section" style={{ paddingTop: 0 }}>
          <GridContainer>
            <Grid row gap>
              <Grid col={12}>
                <h1>Download Module Data</h1>
              </Grid>
            </Grid>

            <Grid row gap>
              <Grid col={8}>
                <p className="query-download-instructions">
                  Use the filtering options below to generate a dataset (in .csv format) of modules according to your
                  selection.
                </p>
              </Grid>
            </Grid>

            <Grid row gap>
              <Grid col={12}>
                {showNoDataAlert && (
                  <div className="no-data-alert-banner">
                    <Alert
                      type="error"
                      headingLevel="h3"
                      heading="Unable to download file: No data matches selected parameters"
                    >
                      <div className="no-data-alert-banner-description">
                        Update filtering options and retry download.
                      </div>
                    </Alert>
                  </div>
                )}
              </Grid>
            </Grid>
          </GridContainer>

          <GridContainer className="query-card-container">
            <Grid className="query-card">
              <Grid row gap>
                <Grid col={12}>
                  <h3 className="query-step-header required-field">Step 1: Select Reporting Cadence</h3>
                  <p className="reporting-cadence-instructions">Select a reporting cadence below.</p>
                  <h4 className="reporting-cadence-title">Reporting Cadence</h4>
                </Grid>
              </Grid>

              <Grid row gap>
                <Grid col={5}>
                  {reportingCadence.map(({ key, label }) =>(
                    <Radio
                      id={`reportingCadenceRadioButton${key}`}
                      name="reportingCadenceRadioButton"
                      className="reporting-cadence-radio-button-selection"
                      label={label}
                      onChange={() => {
                        handleCadenceSelection(key);
                      }}
                    />
                  ))}
                </Grid>
              </Grid>
            </Grid>
          </GridContainer>

          <GridContainer className="query-card-container">
            <Grid className="query-card">
              <Grid row gap>
                <Grid col={12}>
                  <h3 className="query-step-header required-field">Step 2: Select Module</h3>
                  {cadenceSelection === "" ? (
                    <p className="section-subheader">You must select a reporting cadence first.</p>
                  ) : (
                    <p className="section-subheader">Select a module below.</p>
                  )}
                </Grid>
              </Grid>

              <Grid row gap>
                {cadenceSelection === "one_time_annual" && (
                  <>
                    <Grid col={6} className="module-selection-container">
                      <p>One-Time Module Data</p>
                      {oneTimeModules.map(({ key, label }) => (
                        <Radio
                          id={`downloadModuleRadioButton${key}`}
                          name="moduleSelectionRadioButton"
                          className="module-radio-button-selection"
                          label={label}
                          onChange={() => {
                            handleRadioButtonChange(key);
                          }}
                        />
                      ))}
                    </Grid>
                    <Grid col={6} className="module-selection-container">
                      <p>Annual Module Data</p>
                      {annualModules.map(({ key, label }) => (
                        <Radio
                          id={`downloadModuleRadioButton${key}`}
                          name="moduleSelectionRadioButton"
                          className="module-radio-button-selection"
                          label={label}
                          onChange={() => {
                            handleRadioButtonChange(key);
                          }}
                        />
                      ))}
                    </Grid>
                  </>
                )}
              </Grid>

              <Grid row gap>
                {cadenceSelection === "quarterly" && (
                  <Grid col={6}>
                    <p>Quarterly Module Data</p>
                    {quarterlyModules.map(({ key, label }) => (
                      <Radio
                        id={`downloadModuleRadioButton${key}`}
                        name="moduleSelectionRadioButton"
                        className="module-radio-button-selection"
                        label={label}
                        onChange={() => {
                          handleRadioButtonChange(key);
                        }}
                      />
                    ))}
                  </Grid>
                )}
              </Grid>
            </Grid>
          </GridContainer>

          <GridContainer className="query-card-container">
            <Grid className="query-card">
              <Grid row gap>
                <Grid col={12}>
                  <h3 className="query-step-header">Step 3: Select Data Parameters</h3>
                </Grid>
                <Grid col={8}>
                  <p className="data-parameters-instructions">
                    Set the parameters for your data download. Parameters that you set will be applied to all modules
                    that you have selected above.
                  </p>
                </Grid>
              </Grid>

              <Grid className="dropdown-selections">
                <Grid row gap>
                  {yearsList.length > 0 && yearsDataParameter()}

                  {cadenceSelection === "quarterly" && quarterlyCadenceDataParameter()}
                </Grid>

                <Grid row gap>
                  {directRecipientList.length > 1 && directRecipientsDataParameter()}
                </Grid>

                <Grid row gap>
                  {subRecipientsList.length > 0 && subRecipientsDataParameter()}
                </Grid>

                <Grid row gap>
                  {networkProvidersList.length > 0 && networkProvidersDataParameter()}
                </Grid>

                <Grid row gap>
                  {RegisterNonFedFundedStationFeatureFlag === true && federalFundingStatusList.length > 0 && federalFundingStatusParameter()}
                </Grid>

                <Grid row gap>
                  {stationsList.length > 0 && stationsDataParameter()}
                </Grid>
              </Grid>
            </Grid>
          </GridContainer>

          <GridContainer>
            <Grid row gap className="form-query-button-group">
              <ButtonGroup>
                <Button type="button" onClick={handleOpenDownloadData} disabled={selectedRadioButton === 0}>
                  Download Data
                </Button>
                <Button onClick={handleClearFilters} type="button" outline className="clear-filters-button">
                  Clear Filters
                </Button>
              </ButtonGroup>
            </Grid>
          </GridContainer>

          {openDownloadModal && (
            <CSVDownloadModal
              apiPath="download"
              moduleNum={selectedRadioButton.toString()}
              queryParams={queryParams}
              handleShowAlert={handleShowAlert}
              handleHideAlert={handleHideAlert}
              onClose={handleCloseDownloadData}
            />
          )}
        </div>
      </div>
    </div>
  );

  function stationsDataParameter(): React.ReactNode {
    return (
      <Grid col={5}>
        <h4> Station ID or Station Nickname</h4>
        <ComboBox
          key={stationsList.length}
          id={`input-station`}
          name={`input-station`}
          inputProps={stationsSelections.length === 0 ? { placeholder: "All" } : {}}
          options={stationsList}
          onChange={(e) => handleStationChange(e)}
          ref={refStationsComboBox}
        />
        {stationsSelections.map((station) => (
          <Chip key={station} type="selection" className="selected-chip" onDelete={() => handleStationChange(station)}>
            {getLabelFromId(station, stationsList)}
          </Chip>
        ))}
      </Grid>
    );
  }

  function directRecipientsDataParameter(): React.ReactNode {
    return (
      <Grid col={5}>
        <h4> Direct Recipient</h4>
        <ComboBox
          id={`input-subrecipient`}
          name={`input-subrecipient`}
          inputProps={directRecipientSelections.length === 0 ? { placeholder: "All" } : {}}
          options={directRecipientList}
          onChange={(e) => handleDirectRecipientChange(e)}
          ref={refDirectRecipientComboBox}
        />
        {directRecipientSelections.map((dir) => (
          <Chip key={dir} type="selection" className="selected-chip" onDelete={() => handleDirectRecipientChange(dir)}>
            {getLabelFromId(dir, directRecipientList)}
          </Chip>
        ))}
      </Grid>
    );
  }

  function subRecipientsDataParameter(): React.ReactNode {
    return (
      <Grid col={5}>
        <div>
          <h4>
            <Label htmlFor="input-subrecipient">Subrecipient/Contractor</Label>
            <Tooltip
              label="Only data uploaded by the selected Subrecipient(s)/Contractor(s) will be downloaded. Subrecipient(s)/Contractor(s) may be authorized in the station profile for each station."
              asCustom={CustomLink}
            >
              <Icon.InfoOutline className="tooltip-icon tooltip-icon--margin-left-05" />
            </Tooltip>
          </h4>
        </div>
        <ComboBox
          id={`input-subrecipient`}
          name={`input-subrecipient`}
          inputProps={subrecipientSelections.length === 0 ? { placeholder: "All" } : {}}
          options={subRecipientsList}
          onChange={(e) => handleSubrecipientChange(e)}
          ref={refSubrecipientComboBox}
        />
        {subrecipientSelections.map((sub) => (
          <Chip key={sub} type="selection" className="selected-chip" onDelete={() => handleSubrecipientChange(sub)}>
            {getLabelFromId(sub, subRecipientsList)}
          </Chip>
        ))}
      </Grid>
    );
  }

  function networkProvidersDataParameter(): React.ReactNode {
    return (
      <Grid col={5}>
        <h4>
          <Label htmlFor="input-subrecipient">Network Provider</Label>
          <Tooltip
            label="Only data that includes the selected Network Provider(s) will be downloaded. The Network Provider for a given station must be included in each module upload."
            asCustom={CustomLink}
          >
            <Icon.InfoOutline className="tooltip-icon tooltip-icon--margin-left-05" />
          </Tooltip>
        </h4>
        <ComboBox
          id="input-network-provider"
          name="input-network-provider"
          inputProps={networkProviderSelections.length === 0 ? { placeholder: "All" } : {}}
          options={networkProvidersList}
          onChange={(e) => {
            handleNetworkProviderChange(e);
          }}
          ref={refNetworkProviderComboBox}
        />
        {!QueryDownloadRefactorFeatureFlag &&
          networkProviderSelections.map((key: string) => (
              <Chip key={key} type="selection" className="selected-chip" onDelete={() => handleNetworkProviderChange(key)}>
                {getLabelFromId(key, networkProvidersList)}
              </Chip>
            ))
        }
        {QueryDownloadRefactorFeatureFlag &&
          networkProviderSelections.map((uuid) => {
            const networkProviderValue = networkProviderOptions.find((item) => item.network_provider_uuid === uuid)!.network_provider_value;
            return (
              <Chip key={networkProviderValue} type="selection" className="selected-chip" onDelete={() => handleNetworkProviderChange(networkProviderValue)}>
                  {getLabelFromId(networkProviderValue, networkProvidersList)}
              </Chip>
            )
          })
        }
      </Grid>
    );
  }

  function yearsDataParameter(): React.ReactNode {
    return (
      <Grid col={5}>
        <h4> Reporting Year</h4>
        {oneTimeModuleSelected && (
          <p className="reporting-year-disabled-text">Not available when one-time data is selected</p>
        )}
        <ComboBox
          disabled={oneTimeModuleSelected}
          id="input-reporting-years"
          name="input-reporting-years"
          inputProps={reportingYearSelections.length === 0 && !oneTimeModuleSelected ? { placeholder: "All" } : {}}
          options={yearsList}
          onChange={(e) => {
            handleYearChange(e);
          }}
          ref={refReportingYearComboBox}
        />
        {reportingYearSelections.map((year) => (
          <Chip key={year} type="selection" className="selected-chip" onDelete={() => handleYearChange(year)}>
            {year}
          </Chip>
        ))}
      </Grid>
    );
  }

  function quarterlyCadenceDataParameter(): React.ReactNode {
    return (
      <Grid col={5}>
        <h4> Quarter </h4>
        <ComboBox
          id="input-quarterly-cadence"
          name="input-quarterly-cadence"
          inputProps={quartersSelections.length === 0 ? { placeholder: "All" } : {}}
          options={quarterlyCadenceList}
          onChange={(e) => {
            handleQuarterChange(e);
          }}
          ref={refQuartersComboBox}
        />
        {quartersSelections.map((quarter) => (
          <Chip key={quarter} type="selection" className="selected-chip" onDelete={() => handleQuarterChange(quarter)}>
            {getLabelFromId(quarter, quarterlyCadenceList)}
          </Chip>
        ))}
      </Grid>
    );
  }

  function federalFundingStatusParameter(): React.ReactNode {
    return (
      <Grid col={5}>
        <h4>Federal Funding Status </h4>
        <ComboBox
          id="input-federal-funding-status"
          name="input-federal-funding-status"
          inputProps={federalFundingStatusSelections.length === 0 ? { placeholder: "All" }: {}}
          options={federalFundingStatusList}
          onChange={(e) => {
            handleFederalFundingStatusChange(e);
          }}
          ref={refFederalFundingStatusComboBox}
        />
        {federalFundingStatusSelections.map((status) => (
          <Chip key={status} type="selection" className="selected-chip" onDelete={() => handleFederalFundingStatusChange(status)}>
            {getLabelFromId(status, federalFundingStatusList)}
          </Chip>
        ))}
      </Grid>
    );
  }

}

export default QueryDownload;
