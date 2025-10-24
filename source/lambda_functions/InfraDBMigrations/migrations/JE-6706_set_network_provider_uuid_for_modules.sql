-- Populate module tables with the correct uuids from network_providers field will not populate if no network provider match is found
UPDATE module2_data_v3 md 
INNER JOIN network_providers AS np ON md.network_provider_upload = np.network_provider_value 
SET md.network_provider_uuid = np.network_provider_uuid
WHERE md.network_provider_uuid is null; 

UPDATE module3_data_v3 md 
INNER JOIN network_providers AS np ON md.network_provider_upload = np.network_provider_value 
SET md.network_provider_uuid = np.network_provider_uuid
WHERE md.network_provider_uuid is null; 

UPDATE module4_data_v3 md 
INNER JOIN network_providers AS np ON md.network_provider_upload = np.network_provider_value 
SET md.network_provider_uuid = np.network_provider_uuid
WHERE md.network_provider_uuid is null; 

UPDATE module5_data_v3 md 
INNER JOIN network_providers AS np ON md.network_provider_upload = np.network_provider_value 
SET md.network_provider_uuid = np.network_provider_uuid
WHERE md.network_provider_uuid is null; 

UPDATE module6_data_v3 md 
INNER JOIN network_providers AS np ON md.network_provider_upload = np.network_provider_value 
SET md.network_provider_uuid = np.network_provider_uuid
WHERE md.network_provider_uuid is null; 

UPDATE module7_data_v3 md 
INNER JOIN network_providers AS np ON md.network_provider_upload = np.network_provider_value 
SET md.network_provider_uuid = np.network_provider_uuid 
WHERE md.network_provider_uuid is null; 

UPDATE module8_data_v3 md 
INNER JOIN network_providers AS np ON md.network_provider_upload = np.network_provider_value
SET md.network_provider_uuid = np.network_provider_uuid
WHERE md.network_provider_uuid is null; 

UPDATE module9_data_v3 md 
INNER JOIN network_providers AS np ON md.network_provider_upload = np.network_provider_value 
SET md.network_provider_uuid = np.network_provider_uuid
WHERE md.network_provider_uuid is null; 
