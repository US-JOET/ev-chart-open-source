use evchart_data_v3;

ALTER TABLE station_registrations MODIFY COLUMN network_provider VARCHAR(36) NULL;

CREATE TABLE IF NOT EXISTS network_providers(
    np_uuid VARCHAR(36) NOT NULL,
    np_key VARCHAR(45) NOT NULL,
    np_label VARCHAR(45) NOT NULL,
    is_active TINYINT(1) NOT NULL,
    updated_by VARCHAR(72) NULL,
    updated_on DATETIME NULL,
    PRIMARY KEY (`np_uuid`)
);
