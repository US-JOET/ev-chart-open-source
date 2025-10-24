USE evchart_data_v3;
ALTER TABLE station_registrations DROP KEY DR_Station_ID;
ALTER TABLE station_registrations ADD UNIQUE KEY NP_Station_ID (station_id, network_provider);
