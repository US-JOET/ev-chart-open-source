use evchart_data_v3;
ALTER TABLE station_registrations MODIFY address VARCHAR(255);
ALTER TABLE station_registrations MODIFY city VARCHAR(100);
ALTER TABLE station_registrations MODIFY nickname VARCHAR(50);
ALTER TABLE station_registrations MODIFY station_id VARCHAR(36);
ALTER TABLE station_ports MODIFY port_id VARCHAR(36);