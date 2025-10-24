USE evchart_data_v3;
-- Populate columns.
UPDATE station_authorizations SET authorizer = dr_id;
UPDATE station_authorizations SET authorizee = sr_id;
-- Set columns to not be null.
ALTER TABLE station_authorizations MODIFY COLUMN authorizer VARCHAR(36) NOT NULL;
ALTER TABLE station_authorizations MODIFY COLUMN authorizee VARCHAR(36) NOT NULL;
