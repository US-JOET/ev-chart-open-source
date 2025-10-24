USE evchart_data_v3;

-- Add foreign key between network_providers.np_uuid and station_registrations.network_provider
ALTER TABLE station_registrations
ADD CONSTRAINT fk_stationreg_np FOREIGN KEY (network_provider_uuid) REFERENCES network_providers(network_provider_uuid);