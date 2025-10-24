ALTER TABLE station_registrations
ADD PRIMARY KEY (station_uuid);

ALTER TABLE station_authorizations
    ADD CONSTRAINT fk_station_authorizations_station_registrations
    FOREIGN KEY (station_uuid)
    REFERENCES station_registrations(station_uuid);