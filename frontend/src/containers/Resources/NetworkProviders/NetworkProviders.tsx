/**
 * Page displaying list of all network providers.
 * @packageDocumentation
 **/
import { useEffect, useState } from "react";

import { Breadcrumb, BreadcrumbBar, BreadcrumbLink, Grid, GridContainer, Spinner, Table } from "evchartstorybook";

import { PATH_NETWORK_PROVIDERS } from "../../../utils/pathConstants";
import { ROUTE_HOME } from "../../../utils/routeConstants";
import { NetworkProviderInfo } from "interfaces/Organization/organizations-interface";

import "./NetworkProviders.css";

const id_token = localStorage.getItem("id_token");

function NetworkProviders() {
  /**
   * Get the api and base url from the environment variables
   */
  const API_URL = import.meta.env.VITE_API_URL;
  const BASE_URL = import.meta.env.VITE_PUBLIC_URL;

  /**
   * list of network providers from API
   */
  const [networkProviderOptions, setNetworkProviderOptions] = useState<NetworkProviderInfo[]>([]);
  const [isDataLoading, setIsDataLoading] = useState(true);
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
      })
      .finally(() => setIsDataLoading(false));
  }, []);

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
      <Breadcrumb current>
        <span>Network Providers</span>
      </Breadcrumb>
    </BreadcrumbBar>
  );

  return (
    <div>
      <GridContainer>
        <DefaultBreadcrumb />
      </GridContainer>
      <GridContainer className="network-provider-resource">
        <Grid row>
          <Grid col={10}>
            <h1 className="network-provider-heading "> Network Providers </h1>
          </Grid>
        </Grid>
        <Grid row>
          <Grid className="network-provider-subheading-container" col={12}>
            <h2 className="network-provider-subheading"> Network Providers </h2>
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
              <th>Value</th>
              <th>Description</th>
            </thead>
            <tbody>
              {networkProviderOptions.map((item) => (
                <tr key={item.network_provider_value}>
                  <td>{item.network_provider_value}</td>
                  <td>{item.description}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </GridContainer>
    </div>
  );
}

export default NetworkProviders;
