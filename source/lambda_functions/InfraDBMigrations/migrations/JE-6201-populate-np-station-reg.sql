use evchart_data_v3;

-- Rename network_providers np_uuid to network_provider_uuid
ALTER TABLE network_providers CHANGE np_uuid network_provider_uuid VARCHAR(36) NOT NULL;

-- Add NP UUID column to station reg
ALTER TABLE station_registrations
ADD COLUMN network_provider_uuid VARCHAR(36) NULL;

-- Populate station_registrations with the correct uuids from network_providers field 
UPDATE station_registrations sr
INNER JOIN network_providers AS np ON sr.network_provider = np.np_key
SET sr.network_provider_uuid = np.network_provider_uuid