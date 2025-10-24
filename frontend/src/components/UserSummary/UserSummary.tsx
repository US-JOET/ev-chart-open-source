/**
 * Table containing information about all of the organization's users.
 * Imported into the Users view.
 * @packageDocumentation
 **/
import React, { useState, useEffect } from "react";

import { Actions, Button, Chip, Icon, Grid, GridContainer, Pagination, Select, Table, Spinner } from "evchartstorybook";

import { SortState } from "../../interfaces/ui-components-interfaces";

import { isAdmin } from "../../utils/authFunctions";
import { PATH_USERS } from "../../utils/pathConstants";
import { FeatureFlagEnum, getFeatureFlagValue, getFeatureFlagList } from "../../utils/FeatureToggle";
import { ROUTE_USERS } from "../../utils/routeConstants";

import "./UserSummary.css";

interface UserSummaryProps {
  sortByStatus: boolean;
  setRemoveUserModal: () => void;
  setReInviteUserModal: () => void;
  setCurrEmail: (id: string) => void;
  setCurrName: (name: string) => void;
  setCurrRole: (role: string) => void;
}

interface UserAPIResponse {
  first_name: string;
  last_name: string;
  role: string;
  email: string;
  status: string;
}

interface User {
  name: string;
  role: string;
  email: string;
  status: string;
}

export const UserSummary: React.FC<UserSummaryProps> = ({
  sortByStatus,
  setRemoveUserModal,
  setReInviteUserModal,
  setCurrEmail,
  setCurrName,
  setCurrRole,
}): React.ReactElement => {
  /**
   * Feature flag management
   * Toggles the Remove User action from the table
   */
  const [removeUserFeatureFlag, setRemoveUserFeatureFlag] = useState(false);

  /**
   * TODO: UPDATE TO BE REMOVE USER FEATURE FLAG
   */
  useEffect(() => {
    getFeatureFlagList().then((results) => {
      setRemoveUserFeatureFlag(getFeatureFlagValue(results, FeatureFlagEnum.AddUser));
    });
  }, []);

  /**
   * Get the api url from the environment variables
   */
  const API_URL = import.meta.env.VITE_API_URL;

  /**
   * State variable for the list of users
   */
  const [users, setUsers] = useState<User[]>([]);

  /**
   * State variable to check if the API call is still executing
   */
  const [isDataLoading, setIsDataLoading] = useState(true);

  /**
   * Get access token for endpoint authorization
   */
  const id_token = localStorage.getItem("id_token");

  useEffect(() => {
    fetch(`${API_URL}${PATH_USERS}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `${id_token}`,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        setUsers(
          data.map((user: UserAPIResponse) => ({
            name: `${user.first_name} ${user.last_name}`,
            role: user.role,
            email: user.email,
            status: user.status,
          })),
        );
      })
      .catch((err) => {
        console.log(err.message);
      })
      .finally(() => setIsDataLoading(false));
  }, []);

  /**
   * Manages the default sort for rows of data in the user summary table
   */
  const initialSortState: SortState<User> = {
    column: sortByStatus ? "status" : "name",
    direction: sortByStatus ? "desc" : "asc",
  };
  const [sortState, setSortState] = useState(initialSortState);

  /**
   * Set the columns for the table
   */
  const columnHeaders: { key: keyof User; label: string }[] = [
    { key: "name", label: "Name" },
    { key: "role", label: "Role" },
    { key: "email", label: "Email" },
    { key: "status", label: "Status" },
  ];

  /**
   * Change the sort state from user selection
   * @param column the selected column
   */
  const toggleSort = (column: keyof User) => {
    if (column === "name" || column === "role" || column === "email" || column === "status") {
      setSortState((prevState) => ({
        column,
        direction: prevState.column === column && prevState.direction === "asc" ? "desc" : "asc",
      }));
    }
  };

  /**
   * Sort data in table based on the sort state
   */
  const sortedData = [...users].sort((a: User, b: User) => {
    const columnA = a[sortState.column].toUpperCase();
    const columnB = b[sortState.column].toUpperCase();
    const direction = sortState.direction === "asc" ? 1 : -1;
    if (columnA < columnB) return -direction;
    if (columnA > columnB) return direction;
    return 0;
  });

  /**
   * Function to determine which arrow (up, down, double) to render based on current sort state
   * @param column the label for the column being checked
   * @returns the appropriate arrow based on current sort state
   */
  const renderSortArrow = (column: string) => {
    if (column === "name" || column === "role" || column === "email" || column === "status") {
      if (column === sortState.column) {
        if (sortState.direction === "asc") {
          return <Icon.ArrowUpward className="sort-icon" />;
        } else {
          return <Icon.ArrowDownward className="sort-icon" />;
        }
      }
      return <Icon.SortArrow className="sort-icon" />;
    }
  };

  /**
   * Manage pagination
   */
  const [current, setCurrentPage] = useState<number>(1);
  const [itemsPerPage, setItemsPerPage] = useState<number>(25);

  const numberOfPages = sortedData !== undefined ? Math.ceil(sortedData.length / itemsPerPage) : 0;
  const totalItems = sortedData !== undefined ? sortedData.length : 0;

  const startIndex = (Number(current) - 1) * Number(itemsPerPage);
  const endIndex = Number(startIndex) + Number(itemsPerPage);
  const visibleData = sortedData !== undefined ? sortedData.slice(startIndex, endIndex) : [];

  /**
   * Handle user selecting the 'Next' paginated page.
   * Increments the current page number by one.
   */
  const handleNext = () => {
    const nextPage = current + 1;
    setCurrentPage(nextPage);
  };

  /**
   * Handle user selecting the 'Previous' paginated page.
   * Decrements the current page number by one.
   */
  const handlePrevious = () => {
    const prevPage = current - 1;
    setCurrentPage(prevPage);
  };

  /**
   * Handle user moving between paginated pages
   * @param event html mouse event
   * @param pageNum the selected page number
   */
  const handlePageNumber = (event: React.MouseEvent<HTMLButtonElement>, pageNum: number) => {
    setCurrentPage(pageNum);
  };

  /**
   * Update the number of pages based on user selection
   * @param event the selected number of items per page
   */
  const updateNumPages = (event: any) => {
    setItemsPerPage(event);
    setCurrentPage(1);
  };

  /**
   * Render the appropriately styled chip
   * @param status user status (Pending, Active, Expired, Deactivated, Removed)
   * @returns the styled chip
   */
  const ModuleChip = (status: string): React.ReactElement => {
    let moduleChip: React.ReactElement;
    switch (status) {
      case "Pending":
      default:
        moduleChip = <Chip type="warning">Pending</Chip>;
        break;
      case "Active":
        moduleChip = <Chip type="success">Active</Chip>;
        break;
      case "Expired":
        moduleChip = <Chip type="error">Expired</Chip>;
        break;
      case "Deactivated":
        moduleChip = <Chip type="error">Deactivated</Chip>;
        break;
      case "Removed":
        moduleChip = <Chip type="error">Removed</Chip>;
        break;
    }
    return moduleChip;
  };

  const openRemoveUserModal = (id: string) => {
    setCurrEmail(id);
    setRemoveUserModal();
  };

  const openReInviteUserModal = (user: User) => {
    setCurrEmail(user.email);
    setCurrName(user.name);
    setCurrRole(user.role);
    setReInviteUserModal();
  };

  /**
   * Handle removing a user
   * Opens the modal to remove a user
   * @param id the email of the user selected to be removed
   * @returns button to be rendered in the actions dropdown
   */
  const RemoveUser = (id: string) => {
    return (
      <Button type="button" onClick={() => openRemoveUserModal(id)}>
        Remove
      </Button>
    );
  };

  /**
   * Handle re-inviting a user
   * Opens the modal to re-invite a user
   * @param id the email of the user selected
   * @returns button to be rendered in the actions dropdown
   */
  const ReInviteUser = (user: User) => {
    return (
      <Button type="button" onClick={() => openReInviteUserModal(user)}>
        Resend Invite
      </Button>
    );
  };

  /**
   * Get the available actions for a row/user in the table
   * @param item the user information from the current row
   * @returns the set of actions available to users
   */
  const getActions = (item: any) => {
    if (item.status === "Active" && isAdmin()) {
      return (
        <Actions
          item={{
            options: [
              {
                name: "RemoveUser",
                component: RemoveUser(item.email),
              },
            ],
          }}
        />
      );
    } else if ((item.status === "Removed") && isAdmin()) {
      return (
        <Actions
          item={{
            options: [
              {
                name: "ResendInvite",
                component: ReInviteUser(item),
              },
            ],
          }}
        />
      );
      // if status is pending or expired and logged in user is an Admin
    } else if (isAdmin()) {
      return (
        <Actions
          item={{
            options: [
              {
                name: "RemoveUser",
                component: RemoveUser(item.email),
              },
              {
                name: "ResendInvite",
                component: ReInviteUser(item),
              },
            ],
          }}
        />
      );
    } else {
      return <span className="no-actions">—</span>;
    }
  };

  return (
    <div id="SummaryTableUsers" className="summary-table-users" data-testid="SummaryTableUsers">
      {isDataLoading ? (
        <div className="pp-dashboard-spinner-container">
          <div className="pp-dashboard-spinner">
            <Spinner />
          </div>
        </div>
      ) : (
        <>
          <GridContainer className="user-pagination-info">
            <Grid row className="pagination-info-row-container">
              <div className="pagination-info-row">
                {sortedData.length > 10 && (
                  <>
                    <p className="pagination-info-row-count">
                      {startIndex + 1}-{endIndex > totalItems ? totalItems : endIndex} of {totalItems} rows
                    </p>
                    <p className="pagination-info-row-per-page">Rows per page:</p>
                    <Select
                      id="usersSelectItemsPerPage"
                      name="users-select-items-per-page"
                      title="users-select-items-per-page"
                      style={{ width: 90 }}
                      value={itemsPerPage}
                      onChange={(e) => updateNumPages(e.target.value)}
                    >
                      <option value="10">10</option>
                      <option value="25">25</option>
                      <option value="50">50</option>
                      <option value="100">100</option>
                    </Select>
                  </>
                )}
              </div>
            </Grid>
          </GridContainer>
          <Table striped fullWidth bordered={false}>
            <thead>
              <tr>
                {columnHeaders.map(({ key, label }) => (
                  <th className={key} key={key} scope="col" data-testid={key}>
                    <div className="columnHeader" onClick={() => toggleSort(key)}>
                      <span>{label}</span>
                      <span>{renderSortArrow(key)}</span>
                    </div>
                  </th>
                ))}
                {removeUserFeatureFlag && <th className="actions">Actions</th>}
              </tr>
            </thead>
            {users.length === 0 ? (
              <tbody data-testid="noDataAddUser">
                <tr>
                  <td colSpan={columnHeaders.length + 1}>
                    <Grid col={12} className="no-data-add-user" style={{}}>
                      <p>You have not added any users to your organization.</p>
                    </Grid>
                  </td>
                </tr>
              </tbody>
            ) : (
              <tbody data-testid="userData">
                {visibleData.map((item, index) => (
                  <tr className="user-row" data-testid="userRow" key={index}>
                    <td className="user_name overflow-ellipsis">{item.name}</td>
                    <td className="user_role overflow-ellipsis">{item.role}</td>
                    <td className="user_email overflow-ellipsis">{item.email}</td>
                    <td className="user_status overflow-ellipsis">{ModuleChip(item.status)}</td>
                    {removeUserFeatureFlag && <td>{getActions(item)}</td>}
                  </tr>
                ))}
              </tbody>
            )}
          </Table>
          {sortedData.length > 10 && (
            <GridContainer>
              <Grid row style={{ justifyContent: "center" }}>
                <div>
                  <Pagination
                    totalPages={numberOfPages}
                    pathname={ROUTE_USERS}
                    currentPage={current}
                    onClickNext={handleNext}
                    onClickPrevious={handlePrevious}
                    onClickPageNumber={handlePageNumber}
                  />
                </div>
              </Grid>
            </GridContainer>
          )}
        </>
      )}
    </div>
  );
};

export default UserSummary;
