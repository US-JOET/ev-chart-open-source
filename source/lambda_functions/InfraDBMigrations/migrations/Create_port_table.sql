use evchart_data_v3;
CREATE TABLE station_ports (
    station_uuid VARCHAR(36) NOT NULL,     
    port_uuid VARCHAR(36) NOT NULL,
    port_id VARCHAR(30),
    port_type VARCHAR(255),
    federally_funded BOOLEAN, 
    updated_on datetime DEFAULT NULL,
    updated_by VARCHAR(72) DEFAULT NULL,
    PRIMARY KEY (port_uuid)
);


