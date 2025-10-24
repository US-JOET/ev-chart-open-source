/**
 * Footer used through the EV-ChART application.
 * @packageDocumentation
 **/
import React from "react";

import { Grid } from "evchartstorybook";

import splashLogo from "../../../assets/Login_Splash_Graphic.png";
import logoImg from "../../../assets/horizontal_logo-baa57ff6.png";

import "./EVChARTFooter.css";

/**
 * Interface defining the props for the EVChARTFooter
 */
interface EVChARTFooterProps {
  showSplashLogo?: boolean;
}

/**
 * The EV-ChART application footer
 * @param showSplashLogo boolean for if the car splash logo should be rendered
 * @returns the footer as a react component
 */
export const EVChARTFooter: React.FC<EVChARTFooterProps> = ({ showSplashLogo }): React.ReactElement => {
  return (
    <div className="evchart-footer">
      {showSplashLogo && <img className="splash-image" src={splashLogo} />}
      <div className="footer-background">
        <div className="grid-container">
          <Grid row className="footer-content">
            <Grid col={4}>
              <img className="evchart-logo" src={logoImg} alt="Logo for Joint office of Energy and Transportation" />
              <br />
              <div className="evchart-footer-website-links">
                <div>
                  <a href="https://www.energy.gov" target="_blank" className="footer-website-link" rel="noreferrer">
                    energy.gov
                  </a>
                </div>
                <div className="social-link-divider">&nbsp; | &nbsp; </div>
                <div>
                  <a
                    href="https://www.transportation.gov"
                    target="_blank"
                    className="footer-website-link"
                    rel="noreferrer"
                  >
                    transportation.gov
                  </a>
                </div>
              </div>
            </Grid>
            <Grid col={5}>
              <div className="usa-footer__contact-info">
                <p>
                  <span className="tech-assistance-label">Need technical assistance?</span>
                  <br />
                  <a href="https://driveelectric.gov/contact/?inquiry=evchart" target="_blank" rel="noreferrer">
                    Send us a message
                  </a>{" "}
                  or call{" "}
                  <a href="tel:1-833-600-2751" target="_blank" rel="noreferrer">
                    <svg
                      aria-hidden="true"
                      focusable="false"
                      data-prefix="fas"
                      data-icon="phone"
                      className="svg-inline--fa fa-phone template-auto-icon"
                      role="img"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 512 512"
                      height="15.2px"
                      width="15.2px"
                    >
                      <path
                        fill="currentColor"
                        d="M164.9 24.6c-7.7-18.6-28-28.5-47.4-23.2l-88 24C12.1 30.2 0 46 0 64C0 311.4 200.6 512 448 512c18 0 33.8-12.1 38.6-29.5l24-88c5.3-19.4-4.6-39.7-23.2-47.4l-96-40c-16.3-6.8-35.2-2.1-46.3 11.6L304.7 368C234.3 334.7 177.3 277.7 144 207.3L193.3 167c13.7-11.2 18.4-30 11.6-46.3l-40-96z"
                      ></path>
                    </svg>
                    833-600-2751
                  </a>
                  .
                </p>
              </div>
            </Grid>
            <Grid col={3} className="social-container">
              <a
                data-disable-external-link-warning="true"
                href="https://www.linkedin.com/company/joint-office-of-energy-and-transportation"
                target="_blank"
                rel="noreferrer"
              >
                <svg
                  className="svg-inline--fa fa-linkedin fa-2x"
                  aria-hidden="true"
                  focusable="false"
                  data-prefix="fab"
                  data-icon="linkedin"
                  role="img"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 448 512"
                  data-fa-i2svg=""
                  height="32px"
                  width="32px"
                >
                  <path
                    fill="currentColor"
                    d="M416 32H31.9C14.3 32 0 46.5 0 64.3v383.4C0 465.5 14.3 480 31.9 480H416c17.6 0 32-14.5 32-32.3V64.3c0-17.8-14.4-32.3-32-32.3zM135.4 416H69V202.2h66.5V416zm-33.2-243c-21.3 0-38.5-17.3-38.5-38.5S80.9 96 102.2 96c21.2 0 38.5 17.3 38.5 38.5 0 21.3-17.2 38.5-38.5 38.5zm282.1 243h-66.4V312c0-24.8-.5-56.7-34.5-56.7-34.6 0-39.9 27-39.9 54.9V416h-66.4V202.2h63.7v29.2h.9c8.9-16.8 30.6-34.5 62.9-34.5 67.2 0 79.7 44.3 79.7 101.9V416z"
                  ></path>
                </svg>
                <br />
                LinkedIn
              </a>
              <a href="https://www.youtube.com/@jointoffice" target="_blank" rel="noreferrer">
                <svg
                  className="svg-inline--fa fa-youtube fa-2x"
                  aria-hidden="true"
                  focusable="false"
                  data-prefix="fab"
                  data-icon="youtube"
                  role="img"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 576 512"
                  data-fa-i2svg=""
                  height="32px"
                  width="32px"
                >
                  <path
                    fill="currentColor"
                    d="M549.655 124.083c-6.281-23.65-24.787-42.276-48.284-48.597C458.781 64 288 64 288 64S117.22 64 74.629 75.486c-23.497 6.322-42.003 24.947-48.284 48.597-11.412 42.867-11.412 132.305-11.412 132.305s0 89.438 11.412 132.305c6.281 23.65 24.787 41.5 48.284 47.821C117.22 448 288 448 288 448s170.78 0 213.371-11.486c23.497-6.321 42.003-24.171 48.284-47.821 11.412-42.867 11.412-132.305 11.412-132.305s0-89.438-11.412-132.305zm-317.51 213.508V175.185l142.739 81.205-142.739 81.201z"
                  ></path>
                </svg>
                <br />
                YouTube
              </a>
            </Grid>
          </Grid>
        </div>
      </div>
    </div>
  );
};

export default EVChARTFooter;
