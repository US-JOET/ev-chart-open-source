/**
 * Station submission details.
 * @packageDocumentation
 **/
import { FunctionComponent, PropsWithChildren, ReactElement, useEffect, useState } from "react";
import { NavigateOptions, To, useLocation, useNavigate } from "react-router-dom";

import { Tab, Tabs, TabsList, TabPanel } from "@mui/base";
import classNames from "classnames";

import {
  Breadcrumb,
  BreadcrumbBar,
  BreadcrumbLink,
  Button,
  Grid,
  GridContainer,
  Icon,
  Label,
  Select,
  Tooltip,
} from "evchartstorybook";

import { FeatureFlagEnum, getFeatureFlagValue, getFeatureFlagList } from "../../utils/FeatureToggle";
import { PATH_DASHBOARD_SUBMISSION_DETAILS, PATH_REPORTING_YEARS, PATH_STATION_ID } from "../../utils/pathConstants";
import { ROUTE_HOME, ROUTE_NOT_AUTHORIZED, ROUTE_STATION_ID, TabEnum } from "../../utils/routeConstants";

import ColumnDefinitionsModal from "../../components/Modals/ColumnDefinitionModal/ColumnDefinitions";
import StationSubmissionDetailsTable from "../../components/StationSubmissionDetailsTable/StationSubmissionDetailsTable";
import CustomLink from "../../components/Tooltip/tooltips";

import "./StationSubmissionDetails.css";

export interface StationSubmissionDetail {
  module_name: string;
  submission_status: string;
  updated_on: string;
  upload_id: string;
  sub_recipient: string;
}

export interface StationSubmissionDetailsAPIResponse {
  annual: StationSubmissionDetail[];
  one_time: StationSubmissionDetail[];
  quarterly: {
    1: StationSubmissionDetail[];
    2: StationSubmissionDetail[];
    3: StationSubmissionDetail[];
    4: StationSubmissionDetail[];
  };
  submission_details_available: boolean;
}

type CustomBreadcrumbLinkProps = PropsWithChildren<{
  to: To;
  options?: NavigateOptions;
  className?: string;
  customClassName?: string;
}> &
  JSX.IntrinsicElements["button"];

const CustomBreadcrumbLink: FunctionComponent<CustomBreadcrumbLinkProps> = ({
  to,
  options,
  className,
  children,
  customClassName,
  ...buttonProps
}: CustomBreadcrumbLinkProps): ReactElement => {
  const navigate = useNavigate();
  const customBreadcrumbLinkClasses = classNames(className, customClassName);
  return (
    <Button
      className={customBreadcrumbLinkClasses}
      type="button"
      unstyled
      onClick={() => navigate(to, options)}
      {...buttonProps}
    >
      {children}
    </Button>
  );
};

function StationSubmissionDetails() {
  /**
   * Method for changing the location / route
   */
  const navigate = useNavigate();
  const { state } = useLocation();

  /**
   * Get the api and base url from the environment variables
   */
  const API_URL = import.meta.env.VITE_API_URL;
  const BASE_URL = import.meta.env.VITE_PUBLIC_URL;

  /**
   * Get access and id token for endpoint authorization
   */
  const id_token = localStorage.getItem("id_token");

  /**
   * Feature flag management
   */
  const [stationSubmissionDetailsReportingYearFeatureFlag, setStationSubmissionDetailsReportingYearFeatureFlag] =
    useState(false);
  useEffect(() => {
    getFeatureFlagList().then((results) => {
      setStationSubmissionDetailsReportingYearFeatureFlag(
        getFeatureFlagValue(results, FeatureFlagEnum.StationSubmissionDetailsReportingYear),
      );
    });
  }, []);

  /**
   * Split the url to see the station id
   */
  const urlParts = window.location.href.split("/");
  const stationUuid = urlParts[urlParts.length - 1];

  /**
   * Validation
   */
  const initialErrorState = {
    selectedReportingYear: false,
  };
  const [formValidity, setFormValidity] = useState<{ [key: string]: boolean }>(initialErrorState);

  /**
   * State variables
   */
  const [stationNickname, setStationNickname] = useState<string>();
  const [stationId, setStationId] = useState<string>();
  const [stationSubmissionDetails, setStationSubmissionDetails] = useState<StationSubmissionDetailsAPIResponse>({
    quarterly: { 1: [], 2: [], 3: [], 4: [] },
    annual: [],
    one_time: [],
    submission_details_available: false,
  });
  const [isColumnDefinitionsModalOpen, setIsColumnDefinitionsModalOpen] = useState<boolean>(false);

  const [reportingYearList, setReportingYearList] = useState<Array<string>>([]);
  const [isReportingYearListLoading, setIsReportingYearListLoading] = useState<boolean>();
  const [selectedReportingYear, setSelectedReportingYear] = useState<string>(
    state && state.year ? state.year : new Date().getFullYear().toString(),
  );
  const [reportingYearFilter, setReportingYearFilter] = useState<string>(
    state && state.year ? state.year : new Date().getFullYear().toString(),
  );

  useEffect(() => {
    setIsReportingYearListLoading(true);
    fetch(`${API_URL}${PATH_REPORTING_YEARS}`, {
      method: "GET",
      headers: {
        Authorization: `${id_token}`,
      },
    })
      .then((response) => response.json())
      .then((data: { year: string }[]) => {
        const reportingYearOptions: Array<string> = data
          .map((row) => row.year)
          .sort((a, b) => parseInt(b) - parseInt(a));
        setReportingYearList(reportingYearOptions);
      })
      .catch((err) => {
        console.log(err.message);
      })
      .finally(() => setIsReportingYearListLoading(false));
  }, []);

  useEffect(() => {
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
        setStationNickname(data.nickname);
        setStationId(data.station_id);
      })
      .catch((err) => {
        console.log(err.message);
        const errorCode = err.status;
        if (errorCode === 403) {
          navigate(ROUTE_NOT_AUTHORIZED);
        }
      });
  }, []);

  useEffect(() => {
    // Set query parameters based on FT
    const queryParams = stationSubmissionDetailsReportingYearFeatureFlag
      ? `year=${reportingYearFilter}&station=${stationUuid}`
      : `station=${stationUuid}`;

    fetch(`${API_URL}${PATH_DASHBOARD_SUBMISSION_DETAILS}?${queryParams}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
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
        setStationSubmissionDetails(data[0]);
      })
      .catch((err) => {
        console.log(err.message);
      });
  }, [stationSubmissionDetailsReportingYearFeatureFlag, reportingYearFilter]);

  const DefaultBreadcrumb = (): ReactElement => (
    <BreadcrumbBar>
      <Breadcrumb>
        <BreadcrumbLink href={`${BASE_URL}${ROUTE_HOME}`}>
          <span>Home</span>
        </BreadcrumbLink>
      </Breadcrumb>
      <Breadcrumb>
        <BreadcrumbLink<CustomBreadcrumbLinkProps>
          customClassName="station-submission-details__breadcrumb-link"
          asCustom={CustomBreadcrumbLink}
          to="/"
          options={{ state: { startTab: TabEnum.DRSubmissionTracker } }}
        >
          <span>Submission Tracker</span>
        </BreadcrumbLink>
      </Breadcrumb>
      <Breadcrumb current>
        <span>Station Submission Details</span>
      </Breadcrumb>
    </BreadcrumbBar>
  );

  const updateReportingYear = (value: string) => {
    setFormValidity(() => ({
      selectedReportingYear: false,
    }));

    setSelectedReportingYear(value);
  };

  /**
   * Update state variable to trigger back-end filtering
   */
  const updateStationSubmissionDetailsData = () => {
    if (selectedReportingYear === "") {
      setFormValidity({
        selectedReportingYear: true,
      });
    } else {
      setReportingYearFilter(selectedReportingYear);
    }
  };

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
   * Functions to open and close the column definitions modal
   */
  const openColumnDefinitionsModal = () => {
    setIsColumnDefinitionsModalOpen(true);
  };
  const closeColumnDefinitionsModal = () => {
    setIsColumnDefinitionsModalOpen(false);
  };

  return (
    <div className="station-submission-details">
      <GridContainer>
        <DefaultBreadcrumb />
      </GridContainer>
      <div id="StationSubmissionDetails">
        <div className="usa-section" style={{ paddingTop: 0 }}>
          <GridContainer>
            <Grid row>
              <Grid col={9}>
                <h1 className="station-submission-details__heading">Station Submission Details</h1>
                {stationNickname && stationId && (
                  <h2 className="station-submission-details__subheading">
                    {stationNickname} – ID: {stationId}
                  </h2>
                )}
                <p className="station-submission-details__description">
                  View details below to track progress of data for this station that is pending approval, rejected, or
                  approved/submitted. Module data that is in the draft or error states can be viewed in your module
                  submissions.
                </p>
                <p className="station-submission-details__description">
                  <a className="evchart-link" href={`${BASE_URL}${ROUTE_STATION_ID}/${stationUuid}`}>
                    View Station Details
                  </a>
                </p>
              </Grid>
            </Grid>
            {stationSubmissionDetailsReportingYearFeatureFlag && (
              <Grid row gap={3} className="station-submission-details__filters">
                <Grid col={3}>
                  {!isReportingYearListLoading && (
                    <>
                      <div className="label-tooltip-container">
                        <Label htmlFor="selectedReportingYear" className="required-field">
                          Reporting Year
                        </Label>
                        <Tooltip
                          label="The reporting year associated with the submitted module data"
                          asCustom={CustomLink}
                        >
                          <Icon.InfoOutline className="tooltip-icon tooltip-icon--margin-left-05" />
                        </Tooltip>
                      </div>
                      <Select
                        id="selectedReportingYear"
                        name="selectedReportingYear"
                        className={inputValid(formValidity.selectedReportingYear, "field")}
                        onChange={(e) => updateReportingYear(e.target.value)}
                      >
                        {reportingYearList.map((year, index) => {
                          return (
                            <option key={index} value={year}>
                              {year}
                            </option>
                          );
                        })}
                      </Select>
                    </>
                  )}
                </Grid>
                <Grid col>
                  <Button
                    type="button"
                    className="submission-tracker__update-view-button"
                    onClick={updateStationSubmissionDetailsData}
                  >
                    Update View
                  </Button>
                </Grid>
              </Grid>
            )}
            <Grid row>
              <Grid col>
                <Tabs className="station-submission-details__tabs" defaultValue="one-time">
                  <TabsList>
                    <div className="station-submission-details-tab-container">
                      <Tab id="one-time" value="one-time" className="station-submission-details-tab">
                        <div className="station-submission-details-tab__label station-submission-details-tab__label--with-tooltip">
                          One-Time
                          <Tooltip
                            label="Tracking for One Time submissions will roll over from year to year."
                            asCustom={CustomLink}
                          >
                            <Icon.InfoOutline className="info-outline-icon" />
                          </Tooltip>
                        </div>
                      </Tab>
                      <Tab id="annual" value="annual" className="station-submission-details-tab">
                        <div className="station-submission-details-tab__label">Annual</div>
                      </Tab>
                      <Tab id="qrt1" value="qrt1" className="station-submission-details-tab">
                        <div className="station-submission-details-tab__label">
                          <div>Quarter 1</div>
                          <div className="tab-subheading">(Jan-Mar)</div>
                        </div>
                      </Tab>
                      <Tab id="qrt2" value="qrt2" className="station-submission-details-tab">
                        <div className="station-submission-details-tab__label">
                          <div>Quarter 2</div>
                          <div className="tab-subheading">(Apr-Jun)</div>
                        </div>
                      </Tab>
                      <Tab id="qrt3" value="qrt3" className="station-submission-details-tab">
                        <div className="station-submission-details-tab__label">
                          <div>Quarter 3</div>
                          <div className="tab-subheading">(Jul-Sep)</div>
                        </div>
                      </Tab>
                      <Tab id="qrt4" value="qrt4" className="station-submission-details-tab">
                        <div className="station-submission-details-tab__label">
                          <div>Quarter 4</div>
                          <div className="tab-subheading">(Oct-Dec)</div>
                        </div>
                      </Tab>
                    </div>
                  </TabsList>
                  <TabPanel value="one-time" id="one-time">
                    <StationSubmissionDetailsTable
                      stationSubmissionDetails={stationSubmissionDetails.one_time}
                      reportingPeriodColumnLabel="One-Time"
                      setColumnDefinitionsModal={openColumnDefinitionsModal}
                    />
                  </TabPanel>
                  <TabPanel value="annual" id="annual">
                    <StationSubmissionDetailsTable
                      stationSubmissionDetails={stationSubmissionDetails.annual}
                      reportingPeriodColumnLabel="Annual"
                      setColumnDefinitionsModal={openColumnDefinitionsModal}
                    />
                  </TabPanel>
                  <TabPanel id="qrt1" value="qrt1">
                    <StationSubmissionDetailsTable
                      stationSubmissionDetails={stationSubmissionDetails.quarterly[1]}
                      reportingPeriodColumnLabel="Quarter 1"
                      setColumnDefinitionsModal={openColumnDefinitionsModal}
                    />
                  </TabPanel>
                  <TabPanel id="qrt2" value="qrt2">
                    <StationSubmissionDetailsTable
                      stationSubmissionDetails={stationSubmissionDetails.quarterly[2]}
                      reportingPeriodColumnLabel="Quarter 2"
                      setColumnDefinitionsModal={openColumnDefinitionsModal}
                    />
                  </TabPanel>
                  <TabPanel id="qrt3" value="qrt3">
                    <StationSubmissionDetailsTable
                      stationSubmissionDetails={stationSubmissionDetails.quarterly[3]}
                      reportingPeriodColumnLabel="Quarter 3"
                      setColumnDefinitionsModal={openColumnDefinitionsModal}
                    />
                  </TabPanel>
                  <TabPanel id="qrt4" value="qrt4">
                    <StationSubmissionDetailsTable
                      stationSubmissionDetails={stationSubmissionDetails.quarterly[4]}
                      reportingPeriodColumnLabel="Quarter 4"
                      setColumnDefinitionsModal={openColumnDefinitionsModal}
                    />
                  </TabPanel>
                </Tabs>
              </Grid>
            </Grid>
            {isColumnDefinitionsModalOpen && (
              <ColumnDefinitionsModal
                table_name="dr_station_submission_details" // restricted to DR admins
                onClose={closeColumnDefinitionsModal}
              />
            )}
          </GridContainer>
        </div>
      </div>
    </div>
  );
}

export default StationSubmissionDetails;
