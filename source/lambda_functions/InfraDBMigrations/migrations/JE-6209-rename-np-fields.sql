USE evchart_data_v3;

-- Rename np_key and np_label
ALTER TABLE evchart_data_v3.network_providers RENAME COLUMN np_key TO network_provider_value;
ALTER TABLE evchart_data_v3.network_providers RENAME COLUMN np_label TO description;