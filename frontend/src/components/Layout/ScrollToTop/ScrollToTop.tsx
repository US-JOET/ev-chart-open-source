/**
 * Wrapper for all routes to navigate to top of page.
 * @packageDocumentation
 **/
import { useEffect } from "react";
import { useLocation } from "react-router-dom";

/**
 * ScrollToTop function
 * @returns null
 */
const ScrollToTop: React.FC = () => {
  /**
   * useEffect to run any time path changes to autoscroll to top of page
   */
  const { pathname } = useLocation();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  return null;
};

export default ScrollToTop;
