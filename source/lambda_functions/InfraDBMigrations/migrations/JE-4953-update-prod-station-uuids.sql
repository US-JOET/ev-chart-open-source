-- create duplicate of station with new station-uuid and add a COPY_ to the network provider to avoid primary key constrait duplicate error
-- call stored procedure to update old uuid to new uuid
-- delete original station entry
-- update network_provider col of new station entry to remove the COPY_ 

-- CREATING DUPLICIATES OF STATION 
-- 1 adding duplicate station 5041faf8-19e7-11ef-a070-0e47f7cad11d -> f604790e-94d6-4609-8f45-22c7cd839d90
insert into station_registrations(
station_uuid, network_provider, station_id, address, city, dr_id, latitude, longitude, nickname, number_of_ports, ports, project_type, state, status, updated_by, updated_on, zip, zip_extended,
operational_date, NEVI, CFI, EVC_RAA, CMAQ, CRP, OTHER, AFC, num_fed_funded_ports, num_non_fed_funded_ports
)
select "f604790e-94d6-4609-8f45-22c7cd839d90", concat('COPY_', network_provider), station_id, address, city, dr_id, latitude, longitude, nickname, number_of_ports, ports, project_type, state, status, updated_by, updated_on, zip, zip_extended,
operational_date, NEVI, CFI, EVC_RAA, CMAQ, CRP, OTHER, AFC, num_fed_funded_ports, num_non_fed_funded_ports
FROM station_registrations where station_uuid= "5041faf8-19e7-11ef-a070-0e47f7cad11d";


-- 2 adding duplicate station 5041fb4f-19e7-11ef-a070-0e47f7cad11d -> 12cb0e56-0c5a-4747-8666-61fdb408c881
insert into station_registrations(
station_uuid, network_provider, station_id, address, city, dr_id, latitude, longitude, nickname, number_of_ports, ports, project_type, state, status, updated_by, updated_on, zip, zip_extended,
operational_date, NEVI, CFI, EVC_RAA, CMAQ, CRP, OTHER, AFC, num_fed_funded_ports, num_non_fed_funded_ports
)
select "12cb0e56-0c5a-4747-8666-61fdb408c881", concat('COPY_', network_provider), station_id, address, city, dr_id, latitude, longitude, nickname, number_of_ports, ports, project_type, state, status, updated_by, updated_on, zip, zip_extended,
operational_date, NEVI, CFI, EVC_RAA, CMAQ, CRP, OTHER, AFC, num_fed_funded_ports, num_non_fed_funded_ports
FROM station_registrations where station_uuid= "5041fb4f-19e7-11ef-a070-0e47f7cad11d";


-- 3 adding duplicate station 5041fbd6-19e7-11ef-a070-0e47f7cad11d -> 12cb0e56-0c5a-4747-8666-61fdb408c881
insert into station_registrations(
station_uuid, network_provider, station_id, address, city, dr_id, latitude, longitude, nickname, number_of_ports, ports, project_type, state, status, updated_by, updated_on, zip, zip_extended,
operational_date, NEVI, CFI, EVC_RAA, CMAQ, CRP, OTHER, AFC, num_fed_funded_ports, num_non_fed_funded_ports
)
select "8d5b573c-0a32-4f02-b02e-f8119458488b", concat('COPY_', network_provider), station_id, address, city, dr_id, latitude, longitude, nickname, number_of_ports, ports, project_type, state, status, updated_by, updated_on, zip, zip_extended,
operational_date, NEVI, CFI, EVC_RAA, CMAQ, CRP, OTHER, AFC, num_fed_funded_ports, num_non_fed_funded_ports
FROM station_registrations where station_uuid= "5041fbd6-19e7-11ef-a070-0e47f7cad11d";


-- 4 adding duplicate station 5041fc2e-19e7-11ef-a070-0e47f7cad11d -> 29b23c8e-7c89-475c-adaa-9a9c0cd53aa8
insert into station_registrations(
station_uuid, network_provider, station_id, address, city, dr_id, latitude, longitude, nickname, number_of_ports, ports, project_type, state, status, updated_by, updated_on, zip, zip_extended,
operational_date, NEVI, CFI, EVC_RAA, CMAQ, CRP, OTHER, AFC, num_fed_funded_ports, num_non_fed_funded_ports
)
select "29b23c8e-7c89-475c-adaa-9a9c0cd53aa8", concat('COPY_', network_provider), station_id, address, city, dr_id, latitude, longitude, nickname, number_of_ports, ports, project_type, state, status, updated_by, updated_on, zip, zip_extended,
operational_date, NEVI, CFI, EVC_RAA, CMAQ, CRP, OTHER, AFC, num_fed_funded_ports, num_non_fed_funded_ports
FROM station_registrations where station_uuid= "5041fc2e-19e7-11ef-a070-0e47f7cad11d";


-- 5 adding duplicate station 5041fc5a-19e7-11ef-a070-0e47f7cad11d -> 419cda76-786e-43ad-8984-76001c325f37
insert into station_registrations(
station_uuid, network_provider, station_id, address, city, dr_id, latitude, longitude, nickname, number_of_ports, ports, project_type, state, status, updated_by, updated_on, zip, zip_extended,
operational_date, NEVI, CFI, EVC_RAA, CMAQ, CRP, OTHER, AFC, num_fed_funded_ports, num_non_fed_funded_ports
)
select "419cda76-786e-43ad-8984-76001c325f37", concat('COPY_', network_provider), station_id, address, city, dr_id, latitude, longitude, nickname, number_of_ports, ports, project_type, state, status, updated_by, updated_on, zip, zip_extended,
operational_date, NEVI, CFI, EVC_RAA, CMAQ, CRP, OTHER, AFC, num_fed_funded_ports, num_non_fed_funded_ports
FROM station_registrations where station_uuid= "5041fc5a-19e7-11ef-a070-0e47f7cad11d";

-- UPDATING ALL REFERENCES IN MOD TABLES 
-- This script updates the inconsistencies of station_uuids found in the registration table and module tables
-- changes were made to the station_uuids before and the data in prod was never updated, so some DRs/SRs have submitted data for a different station_uuid than what is listed on the station registration table
-- calls stored procedure to update station uuids (old_uuid_list, new_uuid_list)
call update_station_uuids(
    "5041faf8-19e7-11ef-a070-0e47f7cad11d, 5041fb4f-19e7-11ef-a070-0e47f7cad11d, 5041fbd6-19e7-11ef-a070-0e47f7cad11d, 5041fc2e-19e7-11ef-a070-0e47f7cad11d, 5041fc5a-19e7-11ef-a070-0e47f7cad11d",
    "f604790e-94d6-4609-8f45-22c7cd839d90, 12cb0e56-0c5a-4747-8666-61fdb408c881, 8d5b573c-0a32-4f02-b02e-f8119458488b, 29b23c8e-7c89-475c-adaa-9a9c0cd53aa8, 419cda76-786e-43ad-8984-76001c325f37"
) 

-- DELETING OLD STATION_UUIDS
delete from station_registrations where station_uuid = "5041faf8-19e7-11ef-a070-0e47f7cad11d"
delete from station_registrations where station_uuid = "5041fb4f-19e7-11ef-a070-0e47f7cad11d"
delete from station_registrations where station_uuid = "5041fbd6-19e7-11ef-a070-0e47f7cad11d"
delete from station_registrations where station_uuid = "5041fc2e-19e7-11ef-a070-0e47f7cad11d"
delete from station_registrations where station_uuid = "5041fc5a-19e7-11ef-a070-0e47f7cad11d"

-- UPDATING NETWORK PROVIDER IN NEW STATIONS TO REMOVE THE _COPY KEYWORD
update station_registrations SET network_provider = replace(network_provider, "COPY_","") where station_uuid = "f604790e-94d6-4609-8f45-22c7cd839d90";
update station_registrations SET network_provider = replace(network_provider, "COPY_","") where station_uuid = "12cb0e56-0c5a-4747-8666-61fdb408c881";
update station_registrations SET network_provider = replace(network_provider, "COPY_","") where station_uuid = "8d5b573c-0a32-4f02-b02e-f8119458488b";
update station_registrations SET network_provider = replace(network_provider, "COPY_","") where station_uuid = "29b23c8e-7c89-475c-adaa-9a9c0cd53aa8";
update station_registrations SET network_provider = replace(network_provider, "COPY_","") where station_uuid = "419cda76-786e-43ad-8984-76001c325f37";
