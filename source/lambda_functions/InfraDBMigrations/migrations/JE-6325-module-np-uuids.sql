use evchart_data_v3;

-- add column because the previous one does not exist in uppler levels
ALTER TABLE module2_data_v3 ADD network_provider_uuid VARCHAR(36) DEFAULT NULL;
ALTER TABLE module3_data_v3 ADD network_provider_uuid VARCHAR(36) DEFAULT NULL;
ALTER TABLE module4_data_v3 ADD network_provider_uuid VARCHAR(36) DEFAULT NULL;
ALTER TABLE module5_data_v3 ADD network_provider_uuid VARCHAR(36) DEFAULT NULL;
ALTER TABLE module6_data_v3 ADD network_provider_uuid VARCHAR(36) DEFAULT NULL;
ALTER TABLE module7_data_v3 ADD network_provider_uuid VARCHAR(36) DEFAULT NULL;
ALTER TABLE module8_data_v3 ADD network_provider_uuid VARCHAR(36) DEFAULT NULL;
ALTER TABLE module9_data_v3 ADD network_provider_uuid VARCHAR(36) DEFAULT NULL;


-- Populate module tables with the correct uuids from network_providers field 
UPDATE module2_data_v3 md
INNER JOIN network_providers AS np ON md.network_provider_upload = np.np_key
SET md.network_provider_uuid = np.network_provider_uuid;

UPDATE module3_data_v3 md
INNER JOIN network_providers AS np ON md.network_provider_upload = np.np_key
SET md.network_provider_uuid = np.network_provider_uuid;

UPDATE module4_data_v3 md
INNER JOIN network_providers AS np ON md.network_provider_upload = np.np_key
SET md.network_provider_uuid = np.network_provider_uuid;

UPDATE module5_data_v3 md
INNER JOIN network_providers AS np ON md.network_provider_upload = np.np_key
SET md.network_provider_uuid = np.network_provider_uuid;

UPDATE module6_data_v3 md
INNER JOIN network_providers AS np ON md.network_provider_upload = np.np_key
SET md.network_provider_uuid = np.network_provider_uuid;

UPDATE module7_data_v3 md
INNER JOIN network_providers AS np ON md.network_provider_upload = np.np_key
SET md.network_provider_uuid = np.network_provider_uuid;

UPDATE module8_data_v3 md
INNER JOIN network_providers AS np ON md.network_provider_upload = np.np_key
SET md.network_provider_uuid = np.network_provider_uuid;

UPDATE module9_data_v3 md
INNER JOIN network_providers AS np ON md.network_provider_upload = np.np_key
SET md.network_provider_uuid = np.network_provider_uuid;
