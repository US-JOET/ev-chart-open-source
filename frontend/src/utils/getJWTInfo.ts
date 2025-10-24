import { jwtDecode } from "jwt-decode";
import { CustomJwtPayload } from "../interfaces/customJwtPayload";

export const getName = (): string | undefined => {
  const id_token = localStorage.getItem("id_token");
  let name;
  if (id_token) {
    // Pull name from JWT
    const decoded = jwtDecode(id_token) as CustomJwtPayload;
    name = decoded.name;
    if (!name) {
      //If name field not present, combine given + family
      const first_name = decoded.given_name;
      const last_name = decoded.family_name;
      if (first_name && last_name) {
        name = first_name + " " + last_name;
      }
    }
    //If neither present, return email
    if (!name) {
      name = decoded.email;
    }
  }
  //if name found, convert casing
  if (name) {
    name = name.toLowerCase().replace(/(?:^|\s)\w/g, (match) => match.toUpperCase());
  }
  return name;
};

export const getScope = (): string => {
  const id_token = localStorage.getItem("id_token");
  let scope = "";
  if (id_token) {
    // Pull scope from JWT
    const decoded = jwtDecode(id_token) as CustomJwtPayload;
    if (decoded.scope) {
      scope = decoded.scope;
    }
  }
  return scope;
};

export const getStatus = (): string => {
  const id_token = localStorage.getItem("id_token");
  let status = "";
  if (id_token) {
    // Pull scope from JWT
    const decoded = jwtDecode(id_token) as CustomJwtPayload;
    if (decoded.account_status) {
      status = decoded.account_status;
    }
  }
  return status;
};

export const getRole = (): string => {
  const id_token = localStorage.getItem("id_token");
  let role = "";
  if (id_token) {
    // Pull role from JWT
    const decoded = jwtDecode(id_token) as CustomJwtPayload;
    if (decoded.role) {
      role = decoded.role;
    }
  }
  return role;
};

export const getOrgName = (): string => {
  const id_token = localStorage.getItem("id_token");
  let orgName = "";
  if (id_token) {
    // Pull orgName from JWT
    const decoded = jwtDecode(id_token) as CustomJwtPayload;
    if (decoded.org_name) {
      orgName = decoded.org_name;
    }
  }
  return orgName;
};

export const getOrgID = (): string => {
  const id_token = localStorage.getItem("id_token");
  let orgID = "";
  if (id_token) {
    // Pull orgName from JWT
    const decoded = jwtDecode(id_token) as CustomJwtPayload;
    if (decoded.org_id) {
      orgID = decoded.org_id;
    }
  }
  return orgID;
};

export const getOrgFriendlyID = (): string => {
  const id_token = localStorage.getItem("id_token");
  let orgFriendlyID = "";
  if (id_token) {
    // Pull orgName from JWT
    const decoded = jwtDecode(id_token) as CustomJwtPayload;
    if (decoded.org_friendly_id) {
      orgFriendlyID = decoded.org_friendly_id;
    }
  }
  return orgFriendlyID;
};

export const jwtIsExpired = () => {
  const access_token = localStorage.getItem("access_token");
  if (access_token) {
    // Pull expiration from JWT
    const decoded = jwtDecode(access_token) as CustomJwtPayload;
    const tokenExpiration = decoded.exp!;
    const currentTime = Math.floor(Date.now() / 1000);
    return tokenExpiration < currentTime;
  }
};

export const jwtWithin30MinExpiration = () => {
  const access_token = localStorage.getItem("access_token");
  if (access_token) {
    // Pull expiration from JWT
    const decoded = jwtDecode(access_token) as CustomJwtPayload;
    const tokenExpiration = decoded.exp!;
    const currentTime = Math.floor(Date.now() / 1000);
    const secondsToExpiration = tokenExpiration! - currentTime;
    return secondsToExpiration < 1800 && tokenExpiration > currentTime;
  }
};
