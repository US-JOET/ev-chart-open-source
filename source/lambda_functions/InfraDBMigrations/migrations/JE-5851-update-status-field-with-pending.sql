use evchart_data_v3;

-- adding "Pending Approval" as a valid status for the status field in station registrations
ALTER TABLE station_registrations MODIFY status enum("Active", "Pending Approval");