USE evchart_data_v3;

DROP TRIGGER IF EXISTS network_providers_insert_trigger;

INSERT INTO network_providers (network_provider_uuid, network_provider_value, description, is_active)
VALUES (UUID(), "rove", "Rove", 1);

INSERT INTO network_providers (network_provider_uuid, network_provider_value, description, is_active)
VALUES (UUID(), "flitway", "Flitway", 1);

INSERT INTO network_providers (network_provider_uuid, network_provider_value, description, is_active)
VALUES (UUID(), "evium", "EVIUM Charging", 1);