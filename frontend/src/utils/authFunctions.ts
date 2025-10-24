import { redirect } from "react-router-dom";
import { CognitoJwtVerifier } from "aws-jwt-verify";

import { featureFlag } from "../interfaces/featureFlag-interface";

import { FeatureFlagEnum, getFeatureFlagValue } from "./FeatureToggle";
import { getScope, getRole, jwtWithin30MinExpiration } from "./getJWTInfo";
import { PATH_FEATURES, PATH_STATUS, PATH_TOKEN } from "./pathConstants";

import { ROUTE_LOGIN, ROUTE_MAINTENANCE, ROUTE_NOT_AUTHORIZED, ROUTE_NOT_FOUND } from "./routeConstants";

let isRefreshing = false; //flag for token refresh in progress

const BASE_URL = import.meta.env.VITE_PUBLIC_URL;

export async function validateToken() {
  const userPoolId = String(import.meta.env.VITE_USERPOOLID);
  const clientId = String(import.meta.env.VITE_CLIENTID);

  const access_token = localStorage.getItem("access_token");
  const verifier = CognitoJwtVerifier.create({
    userPoolId: userPoolId,
    tokenUse: "access",
    clientId: clientId,
  });
  try {
    if (access_token) {
      await verifier.verify(access_token);
      return true;
    } else {
      window.location.href = `${BASE_URL}${ROUTE_LOGIN}`;
    }
  } catch {
    localStorage.clear();
    window.location.href = `${BASE_URL}${ROUTE_LOGIN}`;
  }
  return false;
}

async function refreshToken() {
  isRefreshing = true; //flag for current token refresh occuring

  const refresh_token = localStorage.getItem("refresh_token");
  const API_URL = import.meta.env.VITE_PUBLIC_URL;
  try {
    const response = await fetch(`${API_URL}${PATH_TOKEN}?refresh=${refresh_token}`, {
      method: "GET",
    });
    if (response.ok) {
      const JwtToken = await response.json();
      localStorage.setItem("access_token", JwtToken.access_token);
      localStorage.setItem("id_token", JwtToken.id_token);
    }
  } catch (error) {
    console.error("An error occurred:", error);
  } finally {
    isRefreshing = false; //reset flag
  }
}

export async function checkMaintenanceMode() {
  const API_URL = import.meta.env.VITE_API_URL;
  try {
    const response = await fetch(`${API_URL}${PATH_STATUS}`, {
      method: "GET",
    });
    if (response.ok) {
      const data = await response.json();
      const maintenanceMode = data.maintenance;
      if (maintenanceMode && !isFederal()) {
        window.location.href = `${BASE_URL}${ROUTE_MAINTENANCE}`;
      }
    }
  } catch (error) {
    console.error("An error occurred:", error);
  }
}

export function checkTokenRefresh() {
  if (jwtWithin30MinExpiration() && !isRefreshing) {
    refreshToken();
  }
}

// reverse_flag is for when you want a false flag to act as a true flag
export async function checkFeatureFlag(featureName: FeatureFlagEnum, reverse_flag: boolean) {
  const API_URL = import.meta.env.VITE_API_URL;
  const BASE_URL = import.meta.env.VITE_PUBLIC_URL;

  let featureIsActive = false;
  try {
    const response = await fetch(`${API_URL}${PATH_FEATURES}`, {
      method: "GET",
    });
    if (response.ok) {
      const data = await response.json();
      const featureList = data as featureFlag[];
      if (featureList) {
        featureIsActive = getFeatureFlagValue(featureList, featureName);

        // featureIsActive  | reverse_flag  | result
        //        true      |       true    | redirect
        //        false     |       false   | redirect
        //        true      |       false   | dont redirect
        //        false     |       true    | dont redirect
        if (featureIsActive === reverse_flag) {
          window.location.href = `${BASE_URL}${ROUTE_NOT_FOUND}`;
        }
      } else {
        console.error("Features Request Failed:", response);
      }
    }
  } catch (error) {
    console.error("An error occurred:", error);
  }
}

// Scope (Org Type) Checks
export function isSRUser() {
  const scope = getScope();
  return scope === "sub-recipient";
}

export function isDRUser() {
  const scope = getScope();
  return scope === "direct-recipient";
}

export function isJOUser() {
  const scope = getScope();
  return scope === "joet";
}

export function isFederal() {
  const scope = getScope();
  return scope === "federal";
}

// Role checks
export function isAdmin() {
  const role = getRole();
  return role.toLowerCase() === "admin";
}

export function DRLoader(admin?: boolean) {
  GeneralAccessLoader();
  if (!isDRUser() || (admin && !isAdmin())) {
    throw redirect(ROUTE_NOT_AUTHORIZED);
  }
  return null;
}

export function SRLoader() {
  GeneralAccessLoader();
  if (!isSRUser()) {
    throw redirect(ROUTE_NOT_AUTHORIZED);
  }
  return null;
}

export function JOLoader() {
  GeneralAccessLoader();
  if (!isJOUser()) {
    throw redirect(ROUTE_NOT_AUTHORIZED);
  }
  return null;
}

export function DROrJOLoader(admin?: boolean) {
  GeneralAccessLoader(admin);
  if (!isDRUser() && !isJOUser()) {
    throw redirect(ROUTE_NOT_AUTHORIZED);
  }
  return null;
}

export function SROrDRLoader(admin?: boolean) {
  GeneralAccessLoader(admin);
  if (!isSRUser() && !isDRUser()) {
    throw redirect(ROUTE_NOT_AUTHORIZED);
  }
  return null;
}

export function  SROrJOLoader(admin?: boolean) {
  GeneralAccessLoader(admin);
  if (!isSRUser() && !isJOUser()) {
    throw redirect(ROUTE_NOT_AUTHORIZED);
  }
  return null;
}

export function GeneralAccessLoader(admin?: boolean) {
  if (admin && !isAdmin()) {
    throw redirect(ROUTE_NOT_AUTHORIZED);
  }
  validateToken();
  checkTokenRefresh();
  checkMaintenanceMode();
  return null;
}

export function FeatureRestrictedLoader(featureFlag: FeatureFlagEnum, admin?: boolean, reverse_flag = false) {
  GeneralAccessLoader(admin);
  checkFeatureFlag(featureFlag, reverse_flag);
  return null;
}

export function JOFeatureRestrictedLoader(featureFlag: FeatureFlagEnum, reverse_flag = false) {
  JOLoader();
  checkFeatureFlag(featureFlag, reverse_flag);
  return null;
}

export function DRFeatureRestrictedLoader(featureFlag: FeatureFlagEnum, admin?: boolean, reverse_flag = false) {
  DRLoader(admin);
  checkFeatureFlag(featureFlag, reverse_flag);
  return null;
}

export function DROrJOFeatureRestrictedLoader(featureFlag: FeatureFlagEnum, reverse_flag = false) {
  DROrJOLoader();
  checkFeatureFlag(featureFlag, reverse_flag);
  return null;
}
