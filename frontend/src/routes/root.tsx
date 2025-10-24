/**
 * Root of the frontend.
 * @packageDocumentation
 **/
import { useState, useEffect } from "react";

import { Outlet } from "react-router-dom";
import { useIdleTimer } from "react-idle-timer";

import EVChARTFooter from "../components/Layout/Footer/EVChARTFooter";
import EVChARTHeader from "../components/Layout/Header/EVChARTHeader";
import ScrollToTop from "../components/Layout/ScrollToTop/ScrollToTop";
import TimeoutModal from "../components/Modals/TimeoutModal/TimeoutModal";
import TermsAndConditionsModal from "../components/Modals/TermsAndConditionsModal/TermsAndConditionsModal";

import { checkTokenRefresh, validateToken } from "../utils/authFunctions";

function Root() {
  const [showTermsModal, setShowTermsModal] = useState<boolean>(false);
  const [showTimeoutModal, setShowTimeoutModal] = useState(false);
  const [isValidUser, setIsValidUser] = useState<boolean>(false);

  const onIdle = () => {
    setShowTimeoutModal(true);
  };

  const onAction = () => {
    checkTokenRefresh();
  };

  const { start } = useIdleTimer({
    onIdle,
    stopOnIdle: true,
    onAction,
    timeout: 1_200_000, // 20 minutes
    throttle: 500,
  });

  const closeTimeoutModal = () => {
    setShowTimeoutModal(false);
    start(); //restart the timer
  };

  async function checkValidUser() {
    const validUser = await validateToken();
    setIsValidUser(validUser);
  }

  useEffect(() => {
    checkValidUser();
  }, []);

  useEffect(() => {
    const termsAccepted = localStorage.getItem("termsAccepted");
    if (!termsAccepted) {
      setShowTermsModal(true);
    }
  }, []);

  const acceptTermsAndConditionsModal = () => {
    setShowTermsModal(false);
  };

  return (
    <>
      {isValidUser && !showTermsModal && (
        <div id="main-content-container">
          <EVChARTHeader />
          <div id="main-content">
            <ScrollToTop />
            <Outlet />
          </div>
          <EVChARTFooter />
        </div>
      )}

      {showTimeoutModal && <TimeoutModal onClose={closeTimeoutModal} />}

      {showTermsModal && <TermsAndConditionsModal onClose={acceptTermsAndConditionsModal} />}
    </>
  );
}

export default Root;
