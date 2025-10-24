/**
 * Header used through the EV-ChART application.
 * @packageDocumentation
 **/
import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";

import classnames from "classnames";

import { GovBanner, Header, NavDropDownButton, NavMenuButton, Menu, PrimaryNav, UserProfile } from "evchartstorybook";

import { isSRUser, isDRUser, isJOUser, isAdmin } from "../../../utils/authFunctions";
import { FeatureFlagEnum, getFeatureFlagValue, getFeatureFlagList } from "../../../utils/FeatureToggle";
import { getName, getOrgFriendlyID, getOrgName } from "../../../utils/getJWTInfo";
import {
  ROUTE_ADD_SR_ORG,
  ROUTE_DIRECT_RECIPIENTS,
  ROUTE_GETTING_STARTED,
  ROUTE_HOME,
  ROUTE_MODULE,
  ROUTE_MODULE_DATA,
  ROUTE_NETWORK_PROVIDERS,
  ROUTE_QUERY_DOWNLOAD,
  ROUTE_STATIONS,
  ROUTE_TECHNICAL_NOTES_PROGRAM_PERFORMANCE,
  ROUTE_USERS,
  SUB_ROUTE_ADD_ORGANIZATION,
  SUB_ROUTE_ADD_USER,
  SUB_ROUTE_DIRECT_RECIPIENTS,
  SUB_ROUTE_GETTING_STARTED,
  SUB_ROUTE_NETWORK_PROVIDERS,
  SUB_ROUTE_PROGRAM_METRICS,
  SUB_ROUTE_STATION_ID,
  SUB_ROUTE_STATION_REGISTRATION,
  SUB_ROUTE_STATIONS,
  SUB_ROUTE_USERS,
} from "../../../utils/routeConstants";

import { SignoutButton } from "../../SignoutButton/SignoutButton";
import headerLogo from "../../../assets/Logo_optional_horizontal.png";
import evchartLogo from "../../../assets/EV-ChART_Text.png";

import "./EVChARTHeader.css";

/**
 * The EV-ChART application header
 * @returns the header as a react component
 */
export const EVChARTHeader = (): React.ReactElement => {
  /**
   * Method for changing the location / route
   */
  const location = useLocation();

  /**
   * Feature flag management
   * * Add SR form (for DRs)
   * * Add Orgs (SR/DR) for JO
   * * Technical Notes for PP for DR
   */
  const [addSROrgFeatureFlag, setAddSROrgFeatureFlag] = useState(false);
  const [joAddOrgFeatureFlag, setJOAddOrgFeatureFlag] = useState(false);
  const [technicalNotesDRPPDashboardFeatureFlag, setTechnicalNotesDRPPDashboardFeatureFlag] = useState(false);
  useEffect(() => {
    getFeatureFlagList().then((results) => {
      setAddSROrgFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.AddSROrg));
      setJOAddOrgFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.JOAddOrg));
      setTechnicalNotesDRPPDashboardFeatureFlag(
        getFeatureFlagValue(results, FeatureFlagEnum.ResourcesTechnicalNotesDRPPDashboard),
      );
    });
  }, []);

  /**
   * State variables for managing header state
   */
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [currentParts, setCurrentParts] = useState<Array<string>>([]);
  const [navDropdownOpen, setNavDropdownOpen] = useState([false, false, false, false, false, false, false, false]);
  const [isHomeCurrent, setHomeCurrent] = useState<boolean>(false);

  /**
   * State variables and useEffect for managing user/ org info for user profile
   */
  const [userName, setUserName] = useState<string>("");
  const [orgName, setOrgName] = useState<string>("");
  const [orgID, setOrgID]  = useState<string>("");
  useEffect(() => {
    const name = getName();
    if (name) {
      setUserName(name);
    }
    setOrgName(getOrgName());
    setOrgID(getOrgFriendlyID())
  }, []);

  /**
   * useEffect to run each time the path changes in order to
   * determine which header part to set as current
   */
  useEffect(() => {
    const urlParts = window.location.href.split("/");
    const currentPage = urlParts[urlParts.length - 1];
    setHomeCurrent(currentPage === "");
    setCurrentParts(urlParts.slice(3, urlParts.length));
  }, [location.pathname]);

  /**
   * All possible routes in the application
   */
  const homeClasses = classnames("usa-nav__link", { "usa-current": isHomeCurrent });
  const data_submittals = [ROUTE_MODULE, ROUTE_MODULE_DATA, ROUTE_QUERY_DOWNLOAD];
  const management = [
    SUB_ROUTE_ADD_USER,
    SUB_ROUTE_STATIONS,
    SUB_ROUTE_STATION_REGISTRATION,
    SUB_ROUTE_STATION_ID,
    SUB_ROUTE_USERS,
    SUB_ROUTE_ADD_ORGANIZATION,
  ];
  const resources = [
    SUB_ROUTE_GETTING_STARTED,
    SUB_ROUTE_NETWORK_PROVIDERS,
    SUB_ROUTE_DIRECT_RECIPIENTS,
    SUB_ROUTE_PROGRAM_METRICS,
  ];

  /**
   * Check if the user is on the current menu item
   * @param path the menu item to check
   * @returns if the current path falls under the menu item being passed
   */
  const checkIsCurrent = (path: string) => {
    if (path === "dataSubmittals") {
      let isDataSubmittal = false;
      currentParts.forEach((part) => {
        if (data_submittals.indexOf(`/${part}`) > -1) {
          isDataSubmittal = true;
        }
      });
      return isDataSubmittal;
    } else if (path === "management") {
      let isManagement = false;
      currentParts.forEach((part) => {
        if (management.indexOf(`/${part}`) > -1) {
          isManagement = true;
        }
      });
      return isManagement;
    } else if (path === "resources") {
      let isResources = false;
      currentParts.forEach((part) => {
        if (resources.indexOf(`/${part}`) > -1) {
          isResources = true;
        }
      });
      return isResources;
    }
  };

  /**
   * Function ties with header nav clicks
   * @param index the index selected
   */
  const handleToggleNavDropdown = (index: number): void => {
    setNavDropdownOpen((prevNavDropdownOpen) => {
      const newOpenState = Array(prevNavDropdownOpen.length).fill(false);
      // eslint-disable-next-line
      newOpenState[index] = !prevNavDropdownOpen[index];
      return newOpenState;
    });
  };

  //
  /**
   * 508 for escaping the menu dropdowns and keeping focus on the parent element
   * @param index selected
   */
  const setFocusNavDropdown = (index: number): void => {
    switch (index) {
      case 1:
        document.getElementById("extended-nav-section-one")?.focus();
        break;
      case 3:
        document.getElementById("extended-nav-section-three")?.focus();
        break;
      case 6:
        document.getElementById("extended-nav-section-six")?.focus();
    }
  };

  /**
   * Function to toggle if the browser or mobile nav should be viewed
   */
  const toggleMobileNav = (): void => {
    setMobileNavOpen((prevOpen) => !prevOpen);
  };

  /**
   * TODO: UPDATE
   * 508 submenu key nav for data submittals
   * @param currElement the menu item the user is currently on
   * @param direction which direction user has selected
   */
  const traverseNavSectionOne = (currElement: string, direction?: string) => {
    if (currElement === "data submittals") {
      document.getElementById("drafts")?.focus();
    } else if (currElement === "drafts" && direction === "down") {
      document.getElementById("submittals")?.focus();
    } else if (currElement === "drafts" && direction === "up") {
      document.getElementById("extended-nav-section-one")?.focus();
    } else if (currElement === "submittals" && direction === "up") {
      document.getElementById("drafts")?.focus();
    }
  };

  /**
   * 508 submenu key nav for management
   * @param currElement the menu item the user is currently on
   * @param direction which direction user has selected
   */
  const traverseNavSectionThree = (currElement: string, direction?: string) => {
    if (currElement === "management") {
      document.getElementById("users")?.focus();
    } else if (currElement === "users" && direction === "down") {
      document.getElementById("stations")?.focus();
    } else if (currElement === "users" && direction === "up") {
      document.getElementById("extended-nav-section-three")?.focus();
    } else if (currElement === "stations") {
      document.getElementById("users")?.focus();
    }
  };

  /**
   * 508 submenu key nav for resources
   * @param currElement the menu item the user is currently on
   * @param direction which direction user has selected
   */
  const traverseNavSectionSix = (currElement: string, direction?: string) => {
    if (currElement === "resources") {
      document.getElementById("getting-started")?.focus();
    } else if (currElement === "getting-started" && direction === "down") {
      document.getElementById("network-providers")?.focus();
    } else if (currElement === "getting-started" && direction === "up") {
      document.getElementById("extended-nav-section-six")?.focus();
    } else if (currElement === "network-providers") {
      if (direction === "down") {
        document.getElementById("technical-notes-pp-dashboard")?.focus();
      } else if (direction === "up") {
        document.getElementById("getting-started")?.focus();
      }
    } else if (currElement === "technical-notes-pp-dashboard") {
      if (direction === "down") {
        document.getElementById("getting-started")?.focus();
      } else if (direction === "up") {
        document.getElementById("network-providers")?.focus();
      }
    }
  };

  /**
   * Primary nav items for sub recipient users
   */
  const SRPrimaryNavItems = [
    <a key="primaryNav_home" className={homeClasses} href={ROUTE_HOME}>
      <span>Home</span>
    </a>,
    <React.Fragment key="primaryNav_1">
      <NavDropDownButton
        menuId="extended-nav-section-one"
        isOpen={navDropdownOpen[1]}
        label="Data Submittals"
        onToggle={(): void => {
          handleToggleNavDropdown(1);
        }}
        onKeyDown={(e: any): void => {
          if (e.keyCode === 27 && navDropdownOpen[1]) {
            handleToggleNavDropdown(1);
            setFocusNavDropdown(1);
          } else if (e.keyCode === 40 && navDropdownOpen[1]) {
            e.preventDefault();
            // Set the first menu child active
            traverseNavSectionOne("data submittals");
          } else if (e.keyCode === 38) {
            e.preventDefault();
          }
        }}
        isCurrent={checkIsCurrent("dataSubmittals")}
        id="extended-nav-section-one"
      />
      <Menu
        id="extended-nav-section-one"
        items={getModuleNavItems()}
        onKeyDown={(e: any): void => {
          if (e.keyCode === 27) {
            handleToggleNavDropdown(1);
            setFocusNavDropdown(1);
          }
        }}
        isOpen={navDropdownOpen[1]}
      />
    </React.Fragment>,
    <React.Fragment key="primaryNav_3">
      <NavDropDownButton
        menuId="extended-nav-section-three"
        isOpen={navDropdownOpen[3]}
        label="Management"
        onToggle={(): void => {
          handleToggleNavDropdown(3);
        }}
        onKeyDown={(e: any): void => {
          if (e.keyCode === 27 && navDropdownOpen[3]) {
            handleToggleNavDropdown(3);
            setFocusNavDropdown(3);
          } else if (e.keyCode === 40 && navDropdownOpen[3]) {
            e.preventDefault();
            // Set the first menu child active
            traverseNavSectionThree("management");
          } else if (e.keyCode === 38) {
            e.preventDefault();
          }
        }}
        isCurrent={checkIsCurrent("management")}
        id="extended-nav-section-three"
      />
      <Menu
        id="extended-nav-section-three"
        items={[
          <a
            href={ROUTE_USERS}
            key="users"
            id="users"
            onKeyDown={(e: any): void => {
              if (e.keyCode === 40) {
                e.preventDefault();
                traverseNavSectionThree("users", "down");
              } else if (e.keyCode === 38) {
                e.preventDefault();
                traverseNavSectionThree("users", "up");
              }
            }}
          >
            Users
          </a>,
          <a
            href={ROUTE_STATIONS}
            key="stations"
            id="stations"
            onKeyDown={(e: any): void => {
              if (e.keyCode === 40) {
                e.preventDefault();
              } else if (e.keyCode === 38) {
                e.preventDefault();
                traverseNavSectionThree("stations");
              }
            }}
          >
            Stations
          </a>,
        ]}
        onKeyDown={(e: any): void => {
          if (e.keyCode === 27) {
            handleToggleNavDropdown(3);
            setFocusNavDropdown(3);
          }
        }}
        isOpen={navDropdownOpen[3]}
      />
    </React.Fragment>,

    <React.Fragment key="primaryNav_6">
      <NavDropDownButton
        menuId="extended-nav-section-six"
        isOpen={navDropdownOpen[6]}
        label="Resources"
        onToggle={(): void => {
          handleToggleNavDropdown(6);
        }}
        onKeyDown={(e: any): void => {
          if (e.keyCode === 27 && navDropdownOpen[6]) {
            handleToggleNavDropdown(6);
            setFocusNavDropdown(6);
          } else if (e.keyCode === 40 && navDropdownOpen[6]) {
            e.preventDefault();
            // Set the first menu child active
            traverseNavSectionSix("resources");
          } else if (e.keyCode === 38) {
            e.preventDefault();
          }
        }}
        isCurrent={checkIsCurrent("resources")}
        id="extended-nav-section-six"
      />
      <Menu
        id="extended-nav-section-six"
        items={[
          (
            <a
              href={ROUTE_DIRECT_RECIPIENTS}
              key="direct-recipients"
              id="direct-recipients"
              onKeyDown={(e: any): void => {
                if (e.keyCode === 40) {
                  e.preventDefault();
                  traverseNavSectionSix("direct-recipients", "down");
                } else if (e.keyCode === 38) {
                  e.preventDefault();
                  traverseNavSectionThree("direct-recipients", "up");
                }
              }}
            >
              Direct Recipient IDs
            </a>
          ),
          <a
            href={ROUTE_NETWORK_PROVIDERS}
            key="network-providers"
            id="network-providers"
            onKeyDown={(e: any): void => {
              if (e.keyCode === 40) {
                e.preventDefault();
                traverseNavSectionSix("network-providers", "down");
              } else if (e.keyCode === 38) {
                e.preventDefault();
                traverseNavSectionThree("network-providers", "up");
              }
            }}
          >
            Network Provider Names
          </a>,
        ]}
        onKeyDown={(e: any): void => {
          if (e.keyCode === 27) {
            handleToggleNavDropdown(6);
            setFocusNavDropdown(6);
          }
        }}
        isOpen={navDropdownOpen[6]}
      />
    </React.Fragment>,
  ];

  /**
   * Primary nav items for direct recipient users
   */
  const DRPrimaryNavItems = [
    <a key="primaryNav_home" className={homeClasses} href={ROUTE_HOME}>
      <span>Home</span>
    </a>,
    <React.Fragment key="primaryNav_1">
      <NavDropDownButton
        menuId="extended-nav-section-one"
        isOpen={navDropdownOpen[1]}
        label="Data Submittals"
        onToggle={(): void => {
          handleToggleNavDropdown(1);
        }}
        onKeyDown={(e: any): void => {
          if (e.keyCode === 27 && navDropdownOpen[1]) {
            handleToggleNavDropdown(1);
            setFocusNavDropdown(1);
          } else if (e.keyCode === 40 && navDropdownOpen[1]) {
            e.preventDefault();
            // Set the first menu child active
            traverseNavSectionOne("data submittals");
          } else if (e.keyCode === 38) {
            e.preventDefault();
          }
        }}
        isCurrent={checkIsCurrent("dataSubmittals")}
        id="extended-nav-section-one"
      />
      <Menu
        id="extended-nav-section-one"
        items={getModuleNavItems()}
        onKeyDown={(e: any): void => {
          if (e.keyCode === 27) {
            handleToggleNavDropdown(1);
            setFocusNavDropdown(1);
          }
        }}
        isOpen={navDropdownOpen[1]}
      />
    </React.Fragment>,
    <React.Fragment key="primaryNav_3">
      <NavDropDownButton
        menuId="extended-nav-section-three"
        isOpen={navDropdownOpen[3]}
        label="Management"
        onToggle={(): void => {
          handleToggleNavDropdown(3);
        }}
        onKeyDown={(e: any): void => {
          if (e.keyCode === 27 && navDropdownOpen[3]) {
            handleToggleNavDropdown(3);
            setFocusNavDropdown(3);
          } else if (e.keyCode === 40 && navDropdownOpen[3]) {
            e.preventDefault();
            // Set the first menu child active
            traverseNavSectionThree("management");
          } else if (e.keyCode === 38) {
            e.preventDefault();
          }
        }}
        isCurrent={checkIsCurrent("management")}
        id="extended-nav-section-three"
      />
      <Menu
        id="extended-nav-section-three"
        items={[
          <a
            href={ROUTE_USERS}
            key="users"
            id="users"
            onKeyDown={(e: any): void => {
              if (e.keyCode === 40) {
                e.preventDefault();
                traverseNavSectionThree("users", "down");
              } else if (e.keyCode === 38) {
                e.preventDefault();
                traverseNavSectionThree("users", "up");
              }
            }}
          >
            Users
          </a>,
          <a
            href={ROUTE_STATIONS}
            key="stations"
            id="stations"
            onKeyDown={(e: any): void => {
              if (e.keyCode === 40) {
                e.preventDefault();
              } else if (e.keyCode === 38) {
                e.preventDefault();
                traverseNavSectionThree("stations");
              }
            }}
          >
            Stations
          </a>,
          addSROrgFeatureFlag && isAdmin() && (
            <a
              href={ROUTE_ADD_SR_ORG}
              key="add-sr-org"
              id="add-sr-org"
              onKeyDown={(e: any): void => {
                if (e.keyCode === 40) {
                  e.preventDefault();
                  traverseNavSectionThree("add-sr-org", "down");
                } else if (e.keyCode === 38) {
                  e.preventDefault();
                  traverseNavSectionThree("add-sr-org", "up");
                }
              }}
            >
              Add Subrecipient/Contractor
            </a>
          ),
        ]}
        onKeyDown={(e: any): void => {
          if (e.keyCode === 27) {
            handleToggleNavDropdown(3);
            setFocusNavDropdown(3);
          }
        }}
        isOpen={navDropdownOpen[3]}
      />
    </React.Fragment>,
    <React.Fragment key="primaryNav_6">
      <NavDropDownButton
        menuId="extended-nav-section-six"
        isOpen={navDropdownOpen[6]}
        label="Resources"
        onToggle={(): void => {
          handleToggleNavDropdown(6);
        }}
        onKeyDown={(e: any): void => {
          if (e.keyCode === 27 && navDropdownOpen[6]) {
            handleToggleNavDropdown(6);
            setFocusNavDropdown(6);
          } else if (e.keyCode === 40 && navDropdownOpen[6]) {
            e.preventDefault();
            // Set the first menu child active
            traverseNavSectionSix("resources");
          } else if (e.keyCode === 38) {
            e.preventDefault();
          }
        }}
        isCurrent={checkIsCurrent("resources")}
        id="extended-nav-section-six"
      />
      <Menu
        id="extended-nav-section-six"
        items={[
          (
            <a
              href={ROUTE_GETTING_STARTED}
              key="getting-started"
              id="getting-started"
              onKeyDown={(e: any): void => {
                if (e.keyCode === 40) {
                  e.preventDefault();
                  traverseNavSectionSix("getting-started", "down");
                } else if (e.keyCode === 38) {
                  e.preventDefault();
                  traverseNavSectionSix("getting-started", "up");
                }
              }}
            >
              Getting Started
            </a>
          ),
          isAdmin() && (
            <a
              href={ROUTE_NETWORK_PROVIDERS}
              key="network-providers"
              id="network-providers"
              onKeyDown={(e: any): void => {
                if (e.keyCode === 40) {
                  e.preventDefault();
                  traverseNavSectionSix("network-providers", "down");
                } else if (e.keyCode === 38) {
                  e.preventDefault();
                  traverseNavSectionSix("network-providers", "up");
                }
              }}
            >
              Network Provider Names
            </a>
          ),
          technicalNotesDRPPDashboardFeatureFlag && (
            <a
              href={ROUTE_TECHNICAL_NOTES_PROGRAM_PERFORMANCE}
              key="technical-notes-pp-dashboard"
              id={"technical-notes-pp-dashboard"}
              onKeyDown={(e: any): void => {
                if (e.keyCode === 40) {
                  e.preventDefault();
                  traverseNavSectionSix("technical-notes-pp-dashboard", "down");
                } else if (e.keyCode === 38) {
                  e.preventDefault();
                  traverseNavSectionSix("technical-notes-pp-dashboard", "up");
                }
              }}
            >
              Dashboard Technical Notes
            </a>
          ),
        ]}
        onKeyDown={(e: any): void => {
          if (e.keyCode === 27) {
            handleToggleNavDropdown(6);
            setFocusNavDropdown(6);
          }
        }}
        isOpen={navDropdownOpen[6]}
      />
    </React.Fragment>,
  ];

  /**
   * Primary nav items for joint office users
   */
  const JOPrimaryNavItems = [
    <a key="primaryNav_home" className={homeClasses} href={ROUTE_HOME}>
      <span>Home</span>
    </a>,
    <React.Fragment key="primaryNav_1">
      <NavDropDownButton
        menuId="extended-nav-section-one"
        isOpen={navDropdownOpen[1]}
        label="Data Submittals"
        onToggle={(): void => {
          handleToggleNavDropdown(1);
        }}
        onKeyDown={(e: any): void => {
          if (e.keyCode === 27 && navDropdownOpen[1]) {
            handleToggleNavDropdown(1);
            setFocusNavDropdown(1);
          } else if (e.keyCode === 40 && navDropdownOpen[1]) {
            e.preventDefault();
            // Set the first menu child active
            traverseNavSectionOne("data submittals");
          } else if (e.keyCode === 38) {
            e.preventDefault();
          }
        }}
        isCurrent={checkIsCurrent("dataSubmittals")}
        id="extended-nav-section-one"
      />
      <Menu
        id="extended-nav-section-one"
        items={getJONavItems()}
        onKeyDown={(e: any): void => {
          if (e.keyCode === 27) {
            handleToggleNavDropdown(1);
            setFocusNavDropdown(1);
          }
        }}
        isOpen={navDropdownOpen[1]}
      />
    </React.Fragment>,

    <React.Fragment key="primaryNav_3">
      <NavDropDownButton
        menuId="extended-nav-section-three"
        isOpen={navDropdownOpen[3]}
        label="Management"
        onToggle={(): void => {
          handleToggleNavDropdown(3);
        }}
        onKeyDown={(e: any): void => {
          if (e.keyCode === 27 && navDropdownOpen[3]) {
            handleToggleNavDropdown(3);
            setFocusNavDropdown(3);
          } else if (e.keyCode === 40 && navDropdownOpen[3]) {
            e.preventDefault();
            document.getElementById("stations")?.focus();
          } else if (e.keyCode === 38) {
            e.preventDefault();
          }
        }}
        isCurrent={checkIsCurrent("management")}
        id="extended-nav-section-three"
      />
      <Menu
        id="extended-nav-section-three"
        items={[
          <a
            href={ROUTE_USERS}
            key="users"
            id="users"
            onKeyDown={(e: any): void => {
              if (e.keyCode === 40) {
                e.preventDefault();
                traverseNavSectionThree("users", "down");
              } else if (e.keyCode === 38) {
                e.preventDefault();
                traverseNavSectionThree("users", "up");
              }
            }}
          >
            Users
          </a>,
          <a
            href={ROUTE_STATIONS}
            key="stations"
            id="stations"
            onKeyDown={(e: any): void => {
              if (e.keyCode === 40) {
                e.preventDefault();
              } else if (e.keyCode === 38) {
                e.preventDefault();
                traverseNavSectionThree("stations");
              }
            }}
          >
            Stations
          </a>,
          joAddOrgFeatureFlag && isAdmin() && (
            <a
              href={ROUTE_ADD_SR_ORG}
              key="add-sr-org"
              id="add-sr-org"
              onKeyDown={(e: any): void => {
                if (e.keyCode === 40) {
                  e.preventDefault();
                  traverseNavSectionThree("add-sr-org", "down");
                } else if (e.keyCode === 38) {
                  e.preventDefault();
                  traverseNavSectionThree("add-sr-org", "up");
                }
              }}
            >
              Add Organization
            </a>
          ),
        ]}
        onKeyDown={(e: any): void => {
          if (e.keyCode === 27) {
            handleToggleNavDropdown(3);
            setFocusNavDropdown(3);
          }
        }}
        isOpen={navDropdownOpen[3]}
      />
    </React.Fragment>,
    <React.Fragment key="primaryNav_6">
      <NavDropDownButton
        menuId="extended-nav-section-six"
        isOpen={navDropdownOpen[6]}
        label="Resources"
        onToggle={(): void => {
          handleToggleNavDropdown(6);
        }}
        onKeyDown={(e: any): void => {
          if (e.keyCode === 27 && navDropdownOpen[6]) {
            handleToggleNavDropdown(6);
            setFocusNavDropdown(6);
          }
        }}
        isCurrent={checkIsCurrent("resources")}
        id="extended-nav-section-six"
      />
      <Menu
        id="extended-nav-section-six"
        items={[
          (
            <a
              href={ROUTE_DIRECT_RECIPIENTS}
              key="direct-recipient-ids"
              id="direct-recipient-ids"
            >
              Direct Recipient IDs
            </a>
          )
        ]}
        onKeyDown={(e: any): void => {
          if (e.keyCode === 27) {
            handleToggleNavDropdown(6);
            setFocusNavDropdown(6);
          }
        }}
        isOpen={navDropdownOpen[6]}
      />
    </React.Fragment>
  ];

  /**
   * Nav items for when user type cannot be determined (error state)
   */
  const EmptyPrimaryNavItems = [
    <a key="primaryNav_home" className="usa-nav__link usa-current" href={ROUTE_HOME}>
      <span>Home</span>
    </a>,
  ];

  /**
   * Function to get the module data nav items
   * @returns the nav items as a react component
   */
  function getModuleNavItems(): React.ReactNode[] {
    const drNavItems = [
      <a
        href={ROUTE_MODULE_DATA}
        key="module-data"
        id="module-data"
        onKeyDown={(e: any): void => {
          if (e.keyCode === 40) {
            e.preventDefault();
            traverseNavSectionOne("module-data", "down");
          } else if (e.keyCode === 38) {
            e.preventDefault();
            traverseNavSectionOne("module-data", "up");
          }
        }}
      >
        Module Data
      </a>,
    ];
    drNavItems.push(
      <a
        href={ROUTE_QUERY_DOWNLOAD}
        key="query-download"
        id="query-download"
        onKeyDown={(e: any): void => {
          if (e.keyCode === 40) {
            e.preventDefault();
          } else if (e.keyCode === 38) {
            e.preventDefault();
            traverseNavSectionOne("query-download");
          }
        }}
      >
        Download Module Data
      </a>,
    );

    return drNavItems;
  }

  /**
   * Function to get the joint office nav items
   * @returns the nav items as a react component
   */
  function getJONavItems(): React.ReactNode[] {
    const joNavItems = [
      <a
        href={ROUTE_MODULE_DATA}
        key="module-data"
        id="module-data"
        onKeyDown={(e: any): void => {
          if (e.keyCode === 40) {
            e.preventDefault();
            traverseNavSectionOne("module-data", "down");
          } else if (e.keyCode === 38) {
            e.preventDefault();
            traverseNavSectionOne("module-data", "up");
          }
        }}
      >
        Module Data
      </a>,
    ];

    joNavItems.push(
      <a
        href={ROUTE_QUERY_DOWNLOAD}
        key="query-download"
        id="query-download"
        onKeyDown={(e: any): void => {
          if (e.keyCode === 40) {
            e.preventDefault();
          } else if (e.keyCode === 38) {
            e.preventDefault();
            traverseNavSectionOne("query-download");
          }
        }}
      >
        Download Module Data
      </a>,
    );

    return joNavItems;
  }

  /**
   * Function to get the header items by user type
   * @returns the appropriate options
   */
  function getHeaderOptions() {
    if (isSRUser()) {
      return SRPrimaryNavItems;
    } else if (isDRUser()) {
      return DRPrimaryNavItems;
    } else if (isJOUser()) {
      return JOPrimaryNavItems;
    } else {
      return EmptyPrimaryNavItems;
    }
  }

  /**
   * Function to truncate the users name if too long
   * @param userName the string name
   * @returns the truncated name, if longer than 30 characters
   */
  function truncateUserName(userName: string): string {
    if (userName.length > 30) {
      return userName.substring(0, 30) + "...";
    } else {
      return userName;
    }
  }

  /**
   * options available on profile menu section
   */
  const options = [
    {
      name: "Sign Out",
      component: <SignoutButton />,
    },
  ];

  return (
    <div className="EVChARTHeader">
      <a className="usa-skipnav" href="#main-content">
        Skip to main content
      </a>
      <GovBanner />
      <div className="jo-header-banner">
        <div className="usa-nav-container">
          <a href="https://driveelectric.gov/" target="_blank" rel="noreferrer">
            <img
              id="evchartHeaderLogo"
              className="evchart-header-logo"
              src={headerLogo}
              alt="Joint Office of Energy and Transportation Logo"
              title="Joint Office of Energy and Transportation Logo"
            />
          </a>
        </div>
      </div>
      <div className={`usa-overlay ${mobileNavOpen ? "is-visible" : ""}`}></div>
      <Header extended={true}>
        <div className="usa-nav-container">
          <div className="usa-navbar">
            <div className="ev-chart-nav-container">
              <a className="logo-title-container" href={ROUTE_HOME}>
                <img
                  id="evchartTextLogo"
                  className="evchart-header-logo"
                  src={evchartLogo}
                  alt="EV-ChART Logo Electric Vehicle Charging Analytics and Reporting Tool"
                  title="EV-ChART Logo Electric Vehicle Charging Analytics and Reporting Tool"
                />
              </a>
              <div className="user-profile-container">
                <UserProfile userName={truncateUserName(userName)} userOrg={orgName} userOrgID={orgID} options={options}></UserProfile>
              </div>
            </div>
            <NavMenuButton label="Menu" onClick={toggleMobileNav} className="usa-menu-btn" />
          </div>
          <PrimaryNav
            aria-label="Primary navigation"
            items={getHeaderOptions()}
            onToggleMobileNav={toggleMobileNav}
            mobileExpanded={mobileNavOpen}
          ></PrimaryNav>
        </div>
      </Header>
    </div>
  );
};

export default EVChARTHeader;
