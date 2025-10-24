USE evchart_data_v3;

DROP TRIGGER IF EXISTS network_providers_update_trigger;
DROP TRIGGER IF EXISTS network_providers_delete_trigger;

ALTER TABLE network_providers_history
RENAME COLUMN np_uuid TO network_provider_uuid;

ALTER TABLE network_providers_history 
ADD CONSTRAINT fk_network_providers FOREIGN KEY (network_provider_uuid) REFERENCES network_providers(network_provider_uuid);