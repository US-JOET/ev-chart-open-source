/**
 * Modal for signout due to user inactivity.
 * @packageDocumentation
 **/
import React, { useState, useEffect } from "react";

import { useIdleTimer } from "react-idle-timer";

import { Button, ButtonGroup, Modal, ModalHeading, ModalFooter } from "evchartstorybook";

import "../Modal.css";

/**
 * Interface defining the props that are passed to the TimeoutModal component
 */
interface TimeoutModalProps {
  onClose: () => void;
}

/**
 * TimeoutModal
 * @param TimeoutModalProps
 * @returns the timeout / inactivity modal
 */
export const TimeoutModal: React.FC<TimeoutModalProps> = ({ onClose }): React.ReactElement => {
  /**
   * Get the api/base url and environment variables
   */
  const API_URL = import.meta.env.VITE_API_URL;
  const hostname = import.meta.env.VITE_HOSTNAME;
  const clientId = import.meta.env.VITE_CLIENTID;
  const region = import.meta.env.VITE_REGION;

  /**
   * State variable for the time remaining
   */
  const [remaining, setRemaining] = useState<number>(600);

  /**
   * Event tied to the signout
   */
  const signOut = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("id_token");
    localStorage.removeItem("refresh_token");
    localStorage.setItem("inactiveSignout", "true");
    window.location.href = `https://${hostname}.auth-fips.${region}.amazoncognito.com/logout?client_id=${clientId}&logout_uri=${API_URL}`;
  };

  /**
   * Event for when the timer completes
   */
  const onIdle = () => {
    signOut();
  };

  /**
   * set the timout function with useIdleTimer
   */
  const { getRemainingTime } = useIdleTimer({
    onIdle,
    events: [],
    timeout: 600_000,
    throttle: 500,
  });

  /**
   * set the remaining time
   */
  useEffect(() => {
    const interval = setInterval(() => {
      setRemaining(Math.ceil(getRemainingTime() / 1000));
    }, 500);

    return () => {
      clearInterval(interval);
    };
  }, []);

  /**
   * Function to format time remaining text in the modal
   * @param seconds the number of seconds remaining
   * @returns the formatted time remaining
   */
  const formatTime = (seconds: number): string => {
    const minutes = Math.ceil(seconds / 60);
    const formattedMinutes = String(minutes);
    const minuteText = minutes === 1 ? "minute" : "minutes";
    return `${formattedMinutes} ${minuteText}`;
  };

  return (
    <div className="timeout-modal">
      <Modal onClose={onClose} aria-labelledby="modal-1-heading" aria-describedby="modal-1-description">
        <ModalHeading id="modal-2-heading">You will be signed out soon</ModalHeading>
        <div className="modal-body">
          <div className="modal-text">
            For your security, you will be signed out in {formatTime(remaining)} due to inactivity.
          </div>
        </div>
        <></>
        <ModalFooter>
          <ButtonGroup>
            <Button onClick={onClose} type="button">
              Stay Signed In
            </Button>
            <Button onClick={signOut} type="button" unstyled className="padding-105 text-center">
              Sign out
            </Button>
          </ButtonGroup>
        </ModalFooter>
      </Modal>
    </div>
  );
};

export default TimeoutModal;
