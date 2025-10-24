USE evchart_data_v3;

-- Set federally funded on port.
UPDATE station_ports SET federally_funded = 1 WHERE port_uuid = 'c51d64d1-6551-11ef-9426-0e47f7cad11d';
