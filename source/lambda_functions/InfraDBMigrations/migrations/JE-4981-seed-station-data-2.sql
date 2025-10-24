USE evchart_data_v3;

-- Set operational dates
UPDATE station_registrations SET operational_date = '2024-04-23' WHERE station_id = 'BradfordChargingStation';
UPDATE station_registrations SET operational_date = '2024-03-20' WHERE station_id = '30589';

-- Correct truncated port_id as well as set type for Tesla Hannaford Rockland
UPDATE station_ports SET port_type = 'DCFC', port_id = 'ec828f0c-b9b1-414a-b766-b4ba2fcbdac3' WHERE port_uuid = 'c51d64d1-6551-11ef-9426-0e47f7cad11d';

-- Add ports for Tesla Hannaford Rockland
INSERT INTO station_ports (port_uuid, port_id, port_type, federally_funded, station_uuid) SELECT uuid(), '9ea105a8-1d67-4627-8935-6f195751199d', 'DCFC', 1, S_Reg.station_uuid FROM station_registrations AS S_Reg WHERE S_Reg.station_id = '30589';
INSERT INTO station_ports (port_uuid, port_id, port_type, federally_funded, station_uuid) SELECT uuid(), '85e48a63-4e57-4a84-9647-a5505d9321ae', 'DCFC', 1, S_Reg.station_uuid FROM station_registrations AS S_Reg WHERE S_Reg.station_id = '30589';
INSERT INTO station_ports (port_uuid, port_id, port_type, federally_funded, station_uuid) SELECT uuid(), '5e7843f1-5561-4eff-924f-0aa04aa3dbfd', 'DCFC', 1, S_Reg.station_uuid FROM station_registrations AS S_Reg WHERE S_Reg.station_id = '30589';
INSERT INTO station_ports (port_uuid, port_id, port_type, federally_funded, station_uuid) SELECT uuid(), '4612ced6-b643-475e-8d33-c4edc03ae2a6', 'DCFC', 1, S_Reg.station_uuid FROM station_registrations AS S_Reg WHERE S_Reg.station_id = '30589';
