USE evchart_data_v3;

ALTER TABLE station_registrations
    DROP INDEX NP_Station_ID,
    ADD UNIQUE KEY NP_Station_ID (station_id, network_provider_uuid);
