USE evchart_data_v3;
-- Allowed to be NULLable columns for now to avoid breaking existing functionality.  To be NOT NULL
-- when cleaning up after implementation.
ALTER TABLE station_authorizations ADD COLUMN authorizer VARCHAR(36);
ALTER TABLE station_authorizations ADD COLUMN authorizee VARCHAR(36);
