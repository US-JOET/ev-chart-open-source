/**
 * The button used to sign the user out of EV-ChART. Imported into the application's header.
 * @packageDocumentation
 **/
import React from "react";

export const SignoutButton: React.FC = (): React.ReactElement => {
  /**
   * Get the environment variables
   */
  const API_URL = import.meta.env.VITE_API_URL;
  const hostname = import.meta.env.VITE_HOSTNAME;
  const clientId = import.meta.env.VITE_CLIENTID;
  const region = import.meta.env.VITE_REGION;

  /**
   * Function to sign out user
   * 
   * - Updates local storage
   * - Redirects the user to the login page
   */
  const signOutUser = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("id_token");
    localStorage.removeItem("refresh_token");
    localStorage.setItem("userSignout", "true");
    window.location.href = `https://${hostname}.auth-fips.${region}.amazoncognito.com/logout?client_id=${clientId}&logout_uri=${API_URL}`;
  };

  return (
    <div className="SignoutButton" style={{ cursor: "pointer" }} onClick={signOutUser}>
      Sign Out
    </div>
  );
};

export default SignoutButton;
