USE evchart_data_v3;

DELETE FROM module5_data_v3
    WHERE upload_id in (
        'e144fa79-19a5-4105-b4cb-a5d930e17544',
        'be883a84-0ee1-4639-af31-8390b1f03913'
    );

DELETE FROM module6_data_v3
    WHERE upload_id in (
        '5f1e3993-7802-47d5-8f4c-c04f92ac4a63',
        'dad18ce2-c41c-420a-85da-9e64e0b5fccf'
    );

DELETE FROM module7_data_v3
    WHERE upload_id in (
        'b05764d7-df33-4d4a-934b-58a6df05d542',
        '24dcdbd3-4906-4160-b8a7-304ca14d2b95'
    );

DELETE FROM module8_data_v3
    WHERE upload_id in (
        '978e7476-67d2-412d-8e44-72e37b4cfa3f',
        'ee257d2a-e2d6-46a7-bff3-5c3808d9bb91'
    );

DELETE FROM module9_data_v3
    WHERE upload_id in (
        '43ddde52-d793-4bb5-9b39-ee072b59d216',
        'a526d759-50ec-4e9e-a086-2c2153ecb4fc'
    );

DELETE FROM import_metadata
    WHERE upload_id in (
        'e144fa79-19a5-4105-b4cb-a5d930e17544',
        'be883a84-0ee1-4639-af31-8390b1f03913',
        '5f1e3993-7802-47d5-8f4c-c04f92ac4a63',
        'dad18ce2-c41c-420a-85da-9e64e0b5fccf',
        'b05764d7-df33-4d4a-934b-58a6df05d542',
        '24dcdbd3-4906-4160-b8a7-304ca14d2b95',
        '978e7476-67d2-412d-8e44-72e37b4cfa3f',
        'ee257d2a-e2d6-46a7-bff3-5c3808d9bb91',
        '43ddde52-d793-4bb5-9b39-ee072b59d216',
        'a526d759-50ec-4e9e-a086-2c2153ecb4fc'
    );

ALTER TABLE module2_data_v3
    ADD CONSTRAINT fk_station_uuid_m2
    FOREIGN KEY (station_uuid)
    REFERENCES station_registrations(station_uuid);

ALTER TABLE module3_data_v3
    ADD CONSTRAINT fk_station_uuid_m3
    FOREIGN KEY (station_uuid)
    REFERENCES station_registrations(station_uuid);

ALTER TABLE module4_data_v3
    ADD CONSTRAINT fk_station_uuid_m4
    FOREIGN KEY (station_uuid)
    REFERENCES station_registrations(station_uuid);

ALTER TABLE module5_data_v3
    ADD CONSTRAINT fk_station_uuid_m5
    FOREIGN KEY (station_uuid)
    REFERENCES station_registrations(station_uuid);

ALTER TABLE module6_data_v3
    ADD CONSTRAINT fk_station_uuid_m6
    FOREIGN KEY (station_uuid)
    REFERENCES station_registrations(station_uuid);

ALTER TABLE module7_data_v3
    ADD CONSTRAINT fk_station_uuid_m7
    FOREIGN KEY (station_uuid)
    REFERENCES station_registrations(station_uuid);

ALTER TABLE module8_data_v3
    ADD CONSTRAINT fk_station_uuid_m8
    FOREIGN KEY (station_uuid)
    REFERENCES station_registrations(station_uuid);

ALTER TABLE module9_data_v3
    ADD CONSTRAINT fk_station_uuid_m9
    FOREIGN KEY (station_uuid)
    REFERENCES station_registrations(station_uuid);
