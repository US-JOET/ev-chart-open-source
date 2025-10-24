/**
 * General maintenance page for the application.
 * @packageDocumentation
 **/
import { Grid, GridContainer } from "evchartstorybook";

import dots_gradient from "../../../assets/dots_gradient.svg";

import "./Maintenance.css";

/**
 * MaintenancePage
 * @returns the maintenance page for the application
 */
function MaintenancePage() {
  return (
    <>
      <div className="maintenance-page">
        <GridContainer>
          <Grid row id="maintenanceText">
            <Grid col={12}>
              <h1 className="align-center">Website is currently under maintenance.</h1>
              <p className="align-center">We'll be back shortly.</p>
            </Grid>
          </Grid>
          <Grid row id="maintenanceDots">
            <Grid col={12}>
              <div className="align-center">
                <img src={dots_gradient} />
              </div>
            </Grid>
          </Grid>
        </GridContainer>
      </div>
    </>
  );
}

export default MaintenancePage;
