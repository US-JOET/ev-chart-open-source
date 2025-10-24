/**
 * Overview of the number of users in the organization.
 * @packageDocumentation
 **/
import React, { useState, useEffect } from "react";
import { Spinner } from "evchartstorybook";
import { PATH_ORG } from "../../utils/pathConstants";

import "./UserOverview.css";

interface OrgInfo {
  org_name: string;
  user_count: string;
}

export const UserOverview: React.FC = (): React.ReactElement => {
  /**
   * Get the api url from the environment variables
   */
  const API_URL = import.meta.env.VITE_API_URL;

  /**
   * State variable with the summary information about the organization
   */
  const [orgSummary, setOrgSummary] = useState<OrgInfo>();

  /**
   * State variable to check if the API call is still executing.
   */
  const [isDataLoading, setIsDataLoading] = useState(true);

  /**
   * Get access token for endpoint authorization
   */
  const id_token = localStorage.getItem("id_token");

  useEffect(() => {
    fetch(`${API_URL}${PATH_ORG}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `${id_token}`,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        setOrgSummary(data);
      })
      .catch((err) => {
        console.log(err.message);
      })
      .finally(() => setIsDataLoading(false));
  }, []);

  /**
   * The table headers
   */
  const headers = [
    { key: "org_name", value: "Organization" },
    { key: "user_count", value: "Total Users" },
  ];

  return (
    <div className="org-summary-background">
      {isDataLoading ? (
        <div className="user-overview-spinner-mini">
          <Spinner />
        </div>
      ) : (
        <div className="org-summary-container">
          {headers.map((orgInfo, index) => (
            <span key={index} className="column">
              <div className="heading">{orgInfo.value}</div>
              <div className="data">{orgSummary![orgInfo.key as keyof OrgInfo]}</div>
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

export default UserOverview;
