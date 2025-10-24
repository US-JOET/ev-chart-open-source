/**
 * Page with all direct recipients and their ids.
 * @packageDocumentation
 **/
import { useEffect, useState } from "react";

import { Breadcrumb, BreadcrumbBar, BreadcrumbLink, Grid, GridContainer, Table, Icon, Spinner } from "evchartstorybook";

import { PATH_DIRECT_RECIPIENTS } from "../../../utils/pathConstants";
import { ROUTE_HOME, ROUTE_QUERY_DOWNLOAD } from "../../../utils/routeConstants";
import { getScope } from "../../../utils/getJWTInfo";

import "./DirectRecipientList.css";

interface DirectRecipient {
  name: string;
  org_id: string;
  org_friendly_id: string;
}

interface SortState {
  column: keyof DirectRecipient;
  direction: string;
}

function DirectRecipientList() {
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
   * list of direct recipients from API
   */
  const [directRecipients, setDirectRecipients] = useState<DirectRecipient[]>([]);
  const [isDataLoading, setIsDataLoading] = useState(true);
  const [recipientType, setRecipientType] = useState("");

  /**
   * Sets the recipient type of the user to render the right table description
   */
  useEffect(() => {
    setRecipientType(getScope());
  }, []);

  /**
   * Get the list of direct recipients
   */
  useEffect(() => {
    fetch(`${API_URL}${PATH_DIRECT_RECIPIENTS}`, {
      method: "GET",
      headers: {
        Authorization: `${id_token}`,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        setDirectRecipients(data);
      })
      .catch((err) => {
        console.log(err.message);
      })
      .finally(() => setIsDataLoading(false));
  }, []);

  /**
   * Manages the default sort for rows of data in the table
   */
  const initialSortState: SortState = {
    column: "name",
    direction: "desc",
  };
  const [sortState, setSortState] = useState(initialSortState);

  /**
   * Change the sort state from user selection
   * @param column the selected column
   */
  const toggleSort = (column: keyof DirectRecipient) => {
    if (column === "name") {
      setSortState((prevState) => ({
        column,
        direction: prevState.column === column && prevState.direction === "asc" ? "desc" : "asc",
      }));
    }
  };

  /**
   * Function to determine which arrow (up, down, double) to render based on current sort state
   * @param column the label for the column being checked
   * @returns the appropriate arrow based on current sort state
   */
  const renderSortArrow = (column: string) => {
    if (column === sortState.column) {
      if (sortState.direction === "asc") {
        return <Icon.ArrowUpward className="sort-icon" />;
      } else {
        return <Icon.ArrowDownward className="sort-icon" />;
      }
    }
    return <Icon.SortArrow className="sort-icon" />;
  };

  /**
   * Sort data in table based on the above sort state
   */
  const sortedData = [...directRecipients].sort((a: DirectRecipient, b: DirectRecipient) => {
    const direction = sortState.direction === "asc" ? 1 : -1;
    const columnA = a[sortState.column].toUpperCase();
    const columnB = b[sortState.column].toUpperCase();
    if (columnA < columnB) return -direction;
    if (columnA > columnB) return direction;
    return 0;
  });

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
      <Breadcrumb>
        <span>Resources</span>
      </Breadcrumb>
      <Breadcrumb current>
        <span>Direct Recipient IDs</span>
      </Breadcrumb>
    </BreadcrumbBar>
  );

  const tableDescriptionForSRUsers = (
    <div className="direct-recipient-instructions">
      <p className="general-instructions">
        When uploading data for multiple direct recipients within one CSV file, ensure that:
      </p>
      <p className="item-instructions">
        1. There is a column titled “direct_recipient_id” in the{" "}
        <a href="https://driveelectric.gov/files/ev-chart-data-input-template.xlsx"> Data Input Template </a> <br></br>
      </p>
      <p className="item-instructions">
        2. Each direct recipient organization for which you are uploading data is represented with its unique ID below
      </p>
    </div>
  );

  const tableDescriptionForJOUsers = (
    <div className="item-instructions">
      <ul>
        <li>
          Subrecipients/contractors use these IDs when uploading data for multiple direct recipients within one CSV file
        </li>
        <li>
          The "Direct Recipient ID" column shown below maps to the "dr_id" column in data downloaded from{" "}
          <a href={ROUTE_QUERY_DOWNLOAD}> Download Module Data </a>{" "}
        </li>
      </ul>
    </div>
  );

  return (
    <div>
      <GridContainer>
        <DefaultBreadcrumb />
      </GridContainer>
      <GridContainer className="direct-recipient-resource">
        <Grid row>
          <Grid col={10}>
            <h1 className="direct-recipient-heading ">Direct Recipient IDs</h1>
            <p className="direct-recipient-subheading">
              Each direct recipient organization has a unique ID within EV-ChART.
            </p>
            {recipientType === "sub-recipient" && tableDescriptionForSRUsers}
            {recipientType === "joet" && tableDescriptionForJOUsers}
          </Grid>
        </Grid>
        {isDataLoading ? (
          <div className="pp-dashboard-spinner-container">
            <div className="pp-dashboard-spinner">
              <Spinner />
            </div>
          </div>
        ) : (
          <Table striped fullWidth bordered={false}>
            <thead>
              <th>Direct Recipient ID</th>
              <th key={"org-name"} scope="col">
                <div className="columnHeader" onClick={() => toggleSort("name")}>
                  <span>Direct Recipient Organization Name</span>
                  <span>{renderSortArrow("name")}</span>
                </div>
              </th>
            </thead>
            <tbody>
              {Object.entries(sortedData).map(([, value], index) => (
                <tr key={index}>
                  <td>{value.org_friendly_id}</td>
                  <td>{value.name}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </GridContainer>
    </div>
  );
}

export default DirectRecipientList;
