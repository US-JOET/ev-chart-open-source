USE evchart_data_v3;

ALTER TABLE module2_data_v3
    ADD CONSTRAINT fk_module2_data_v3_station_ports
    FOREIGN KEY (port_uuid)
    REFERENCES station_ports(port_uuid);

ALTER TABLE module3_data_v3
    ADD CONSTRAINT fk_module3_data_v3_station_ports
    FOREIGN KEY (port_uuid)
    REFERENCES station_ports(port_uuid);

ALTER TABLE module4_data_v3
    ADD CONSTRAINT fk_module4_data_v3_station_ports
    FOREIGN KEY (port_uuid)
    REFERENCES station_ports(port_uuid);
