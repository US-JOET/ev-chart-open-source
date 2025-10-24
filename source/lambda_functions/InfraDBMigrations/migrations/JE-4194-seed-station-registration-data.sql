USE evchart_data_v3;
-- For number of ports, can we leave totals of 0 as NULL?
UPDATE station_registrations SET AFC = 1, num_fed_funded_ports = 4, NEVI = 1, operational_date = '2023-12-15' WHERE station_id = '140109';
UPDATE station_registrations SET AFC = 1, num_fed_funded_ports = 4, NEVI = 1, operational_date = '2023-12-23' WHERE station_id = '700083';
UPDATE station_registrations SET AFC = 1, num_fed_funded_ports = 4, NEVI = 1, operational_date = '2024-03-08' WHERE station_id = '701127';
UPDATE station_registrations SET AFC = 1, num_fed_funded_ports = 4, NEVI = 1, operational_date = '2023-12-08' WHERE station_id = '61341';
UPDATE station_registrations SET AFC = 1, num_fed_funded_ports = 4, NEVI = 1, operational_date = '2023-12-21' WHERE station_id = '62241';
UPDATE station_registrations SET AFC = 1, num_fed_funded_ports = 5, num_non_fed_funded_ports = 3, NEVI = 1 WHERE station_id = '30589';
UPDATE station_registrations SET AFC = 1, num_fed_funded_ports = 4, num_non_fed_funded_ports = 4, NEVI = 1 WHERE station_id = 'BradfordChargingStation';
UPDATE station_registrations SET AFC = 1, num_fed_funded_ports = 4, NEVI = 1, operational_date = '2024-07-17' WHERE station_id = 'RI-HOPKINTON-00001';
UPDATE station_registrations SET AFC = 1, num_fed_funded_ports = 2, num_non_fed_funded_ports = 4, NEVI = 1, operational_date = '2024-07-17' WHERE station_id = 'RI-WARWICK-00001';
UPDATE station_registrations SET AFC = 1, num_fed_funded_ports = 4, NEVI = 1, operational_date = '2024-03-04' WHERE station_id = '11e7a34f-88ba-4729-803d-06a5616afd69';
UPDATE station_registrations SET AFC = 1, num_fed_funded_ports = 2, num_non_fed_funded_ports = 2, NEVI = 1, operational_date = '2024-06-18' WHERE station_id = 'PA-EMLENTON-00001';
UPDATE station_registrations SET AFC = 1, num_fed_funded_ports = 4, NEVI = 1, operational_date = '2024-06-18' WHERE station_id = '701142';
UPDATE station_registrations SET AFC = 1, num_fed_funded_ports = 4, NEVI = 1, operational_date = '2024-06-24' WHERE station_id = '217';
UPDATE station_registrations SET AFC = 1, num_fed_funded_ports = 4, NEVI = 1, operational_date = '2024-07-03' WHERE station_id = '218';
UPDATE station_registrations SET AFC = 1, num_fed_funded_ports = 4, NEVI = 1, operational_date = '2024-06-07' WHERE station_id = '67346';

-- EVolveNY - Kingston
UPDATE station_ports AS S_Port INNER JOIN station_registrations AS S_Reg ON S_Port.station_uuid = S_Reg.station_uuid SET port_type = "DCFC", federally_funded = 1 WHERE S_Reg.station_id = '140109';

-- EVolveNY - Richmondville
UPDATE station_ports AS S_Port INNER JOIN station_registrations AS S_Reg ON S_Port.station_uuid = S_Reg.station_uuid SET port_type = "DCFC", federally_funded = 1 WHERE S_Reg.station_id = '700083';

-- EVolveNY – North Hudson
UPDATE station_ports AS S_Port INNER JOIN station_registrations AS S_Reg ON S_Port.station_uuid = S_Reg.station_uuid SET port_type = "DCFC", federally_funded = 1 WHERE S_Reg.station_id = '701127';

-- Pilot-70-B-#454
UPDATE station_ports AS S_Port INNER JOIN station_registrations AS S_Reg ON S_Port.station_uuid = S_Reg.station_uuid SET port_type = "DCFC", federally_funded = 1 WHERE S_Reg.station_id = '61341';

-- Pilot Pittston 370 
UPDATE station_ports AS S_Port INNER JOIN station_registrations AS S_Reg ON S_Port.station_uuid = S_Reg.station_uuid SET port_type = "DCFC", federally_funded = 1 WHERE S_Reg.station_id = '62241';

-- Tesla Hannaford Rockland has one port already, but spreadsheet has no further specific port information to actually seed.

-- Bradford (are ports fed funded and non-fed funded both?) has no existing ports for this station.
INSERT INTO station_ports (port_uuid, port_id, port_type, federally_funded, station_uuid) SELECT uuid(), 'T184-US2-1024-012', 'DCFC', 1, S_Reg.station_uuid FROM station_registrations AS S_Reg WHERE S_Reg.station_id = 'BradfordChargingStation';
INSERT INTO station_ports (port_uuid, port_id, port_type, federally_funded, station_uuid) SELECT uuid(), 'T184-US2-1124-002', 'DCFC', 1, S_Reg.station_uuid FROM station_registrations AS S_Reg WHERE S_Reg.station_id = 'BradfordChargingStation';
INSERT INTO station_ports (port_uuid, port_id, port_type, federally_funded, station_uuid) SELECT uuid(), 'T184-US2-1124-006', 'DCFC', 1, S_Reg.station_uuid FROM station_registrations AS S_Reg WHERE S_Reg.station_id = 'BradfordChargingStation';
INSERT INTO station_ports (port_uuid, port_id, port_type, federally_funded, station_uuid) SELECT uuid(), 'T184-US2-1124-007', 'DCFC', 1, S_Reg.station_uuid FROM station_registrations AS S_Reg WHERE S_Reg.station_id = 'BradfordChargingStation';

-- NEVI Hopkinton Park & Ride has no port information.
-- NEVI Warwick park and ride has no port information.

-- Maui – Kahului Park & Ride
UPDATE station_ports AS S_Port INNER JOIN station_registrations AS S_Reg ON S_Port.station_uuid = S_Reg.station_uuid SET port_type = "DCFC", federally_funded = 1 WHERE S_Reg.station_id = '11e7a34f-88ba-4729-803d-06a5616afd69';

-- Emlenton Truck Plaza
UPDATE station_ports AS S_Port INNER JOIN station_registrations AS S_Reg ON S_Port.station_uuid = S_Reg.station_uuid SET port_type = "DCFC" WHERE S_Reg.station_id = 'PA-EMLENTON-00001' AND S_Port.port_id IN ('USCPIE14032141*1','USCPIE14033171*1');
UPDATE station_ports AS S_Port INNER JOIN station_registrations AS S_Reg ON S_Port.station_uuid = S_Reg.station_uuid SET port_type = "DCFC", federally_funded = 1 WHERE S_Reg.station_id = 'PA-EMLENTON-00001' AND S_Port.port_id IN ('USCPIE15934791*1','USCPIE15934791*2');

-- Moab
UPDATE station_ports AS S_Port INNER JOIN station_registrations AS S_Reg ON S_Port.station_uuid = S_Reg.station_uuid SET port_type = "DCFC", federally_funded = 1 WHERE S_Reg.station_id = '701142';

-- Francis-75-E-Caseys3535
UPDATE station_ports AS S_Port INNER JOIN station_registrations AS S_Reg ON S_Port.station_uuid = S_Reg.station_uuid SET port_type = "DCFC", federally_funded = 1 WHERE S_Reg.station_id = '217';

-- Francis-77-B-DG-Byesville
UPDATE station_ports AS S_Port INNER JOIN station_registrations AS S_Reg ON S_Port.station_uuid = S_Reg.station_uuid SET port_type = "DCFC", federally_funded = 1 WHERE S_Reg.station_id = '218';

-- Pilot-71-C-#455
UPDATE station_ports AS S_Port INNER JOIN station_registrations AS S_Reg ON S_Port.station_uuid = S_Reg.station_uuid SET port_type = "DCFC", federally_funded = 1 WHERE S_Reg.station_id = '67346';
