/**
 * Index.tsx.
 * @packageDocumentation
 **/
import React from "react";
import ReactDOM from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";

import { FeatureFlagEnum } from "./utils/FeatureToggle";

/**
 * Route constants
 */
import {
  ROUTE_ADD_SR_ORG,
  ROUTE_ADD_USER,
  ROUTE_AUTHROIZE_CONTRACTORS,
  ROUTE_DIRECT_RECIPIENTS,
  ROUTE_EDIT,
  ROUTE_GETTING_STARTED,
  ROUTE_HISTORY,
  ROUTE_HOME,
  ROUTE_LOGIN,
  ROUTE_MAINTENANCE,
  ROUTE_MODULE,
  ROUTE_MODULE_DATA,
  ROUTE_NETWORK_PROVIDERS,
  ROUTE_NOT_AUTHORIZED,
  ROUTE_QUERY_DOWNLOAD,
  ROUTE_STATION_ID,
  ROUTE_STATION_REGISTRATION,
  ROUTE_STATION_SUBMISSION_DETAILS,
  ROUTE_STATIONS,
  ROUTE_TECHNICAL_NOTES_PROGRAM_PERFORMANCE,
  ROUTE_USERS,
} from "./utils/routeConstants";

/**
 * General screens
 */
import Root from "./routes/root";
import Login from "./containers/Login/Login";
import Maintenance from "./containers/AppElements/Maintenance/Maintenance";
import HomeRoute from "./containers/Home/HomeRoute/HomeRoute";
import ErrorPage from "./containers/AppElements/ErrorPage/ErrorPage";
import NotAuthorized from "./containers/AppElements/NotAuthorized/NotAuthorized";
import StationDetails from "./containers/Management/Stations/StationDetails/StationDetails";
import QueryDownload from "./containers/QueryDownload/QueryDownload";
import ModuleDetails from "./containers/ModuleDetails/ModuleDetails";
import Stations from "./containers/Management/Stations/StationsHome/Stations";
import Users from "./containers/Management/Users/UsersHome/Users";
import AddUser from "./containers/Management/Users/AddUser/AddUser";
import ModuleData from "./containers/ModuleData/ModuleData";
import NetworkProviders from "./containers/Resources/NetworkProviders/NetworkProviders";

/**
 * Sub-recipient only screens
 */
import DirectRecipientList from "./containers/Resources/DirectRecipients/DirectReciepientList";

/**
 * Direct recipient only screens
 */
import AddOrg from "./containers/Management/AddOrg/AddOrg";
import StationForm from "./containers/Management/Stations/StationForm/StationForm";
import GettingStarted from "./containers/Resources/GettingStarted/GettingStarted";
import TechnicalNotesProgramPerformance from "./containers/Resources/TechnicalNotesProgramPerformance/TechnicalNotesProgramPerformance";
import StationSubmissionDetails from "./containers/StationSubmissionDetails/StationSubmissionDetails";

import {
  DRFeatureRestrictedLoader,
  GeneralAccessLoader,
  FeatureRestrictedLoader,
  DROrJOFeatureRestrictedLoader,
  SRLoader,
  DROrJOLoader,
  DRLoader,
  SROrDRLoader,
  SROrJOLoader
} from "./utils/authFunctions";

import "./App.css";

const routes = [
  {
    path: ROUTE_LOGIN,
    element: <Login />,
    errorElement: <ErrorPage />,
  },
  {
    path: ROUTE_MAINTENANCE,
    element: <Maintenance />,
  },
  {
    path: ROUTE_NOT_AUTHORIZED,
    element: <NotAuthorized />,
    errorElement: <ErrorPage />,
  },
  {
    path: ROUTE_HOME,
    element: <Root />,
    errorElement: <ErrorPage />,
    children: [
      {
        path: ROUTE_HOME,
        loader: () => {
          return GeneralAccessLoader();
        },
        element: <HomeRoute />,
      },
      {
        path: ROUTE_MODULE_DATA,
        loader: () => {
          return GeneralAccessLoader();
        },
        element: <ModuleData />,
      },
      {
        path: `${ROUTE_MODULE}/:uploadId`,
        loader: () => {
          return GeneralAccessLoader();
        },
        element: <ModuleDetails />,
      },
      {
        path: `${ROUTE_MODULE}/:uploadId${ROUTE_HISTORY}`,
        loader: () => {
          return GeneralAccessLoader(true);
        },
        element: <ModuleDetails />,
      },
      {
        path: ROUTE_STATIONS,
        loader: () => {
          return GeneralAccessLoader();
        },
        element: <Stations />,
      },
      {
        path: `${ROUTE_STATION_SUBMISSION_DETAILS}/:stationId`,
        loader: () => {
          return DRFeatureRestrictedLoader(FeatureFlagEnum.StationSubmissionDetails);
        },
        element: <StationSubmissionDetails />,
      },
      {
        path: ROUTE_QUERY_DOWNLOAD,
        loader: () => {
          return DROrJOLoader();
        },
        element: <QueryDownload />,
      },
      {
        path: ROUTE_STATION_REGISTRATION,
        loader: () => {
          return SROrDRLoader(true);
        },
        element: <StationForm />,
      },
      {
        path: `${ROUTE_STATION_ID}/:stationId`,
        loader: () => {
          return GeneralAccessLoader();
        },
        element: <StationDetails />,
      },
      {
        path: `${ROUTE_STATION_ID}/:stationId${ROUTE_EDIT}`,
        loader: () => {
          return DRLoader(true);
        },
        element: <StationForm />,
      },
      {
        path: `${ROUTE_STATION_ID}/:stationId${ROUTE_AUTHROIZE_CONTRACTORS}`,
        loader: () => {
          return SRLoader();
        },
        element: <StationDetails />,
      },
      {
        path: ROUTE_USERS,
        loader: () => {
          return GeneralAccessLoader();
        },
        element: <Users />,
      },
      {
        path: ROUTE_ADD_USER,
        loader: () => {
          return FeatureRestrictedLoader(FeatureFlagEnum.AddUser, true);
        },
        element: <AddUser />,
      },
      {
        path: ROUTE_ADD_SR_ORG,
        loader: () => {
          return DROrJOLoader(true);
        },
        element: <AddOrg />,
      },
      {
        path: ROUTE_NETWORK_PROVIDERS,
        loader: () => {
          return SROrDRLoader(true);
        },
        element: <NetworkProviders />,
      },
      {
        path: ROUTE_DIRECT_RECIPIENTS,
        loader: () => {
          return SROrJOLoader(true);
        },
        element: <DirectRecipientList />,
      },
      {
        path: ROUTE_GETTING_STARTED,
        loader: () => {
          return DRLoader();
        },
        element: <GettingStarted />,
      },
      {
        path: ROUTE_TECHNICAL_NOTES_PROGRAM_PERFORMANCE,
        loader: () => {
          return DROrJOFeatureRestrictedLoader(FeatureFlagEnum.ResourcesTechnicalNotesDRPPDashboard);
        },
        element: <TechnicalNotesProgramPerformance />,
      },
    ],
  },
];

const router = createBrowserRouter(routes, {
  basename: import.meta.env.VITE_BASE_NAME,
});

const root = ReactDOM.createRoot(document.getElementById("root") as HTMLElement);

root.render(
  <React.StrictMode>
    <>
      <RouterProvider router={router}></RouterProvider>
    </>
  </React.StrictMode>,
);
