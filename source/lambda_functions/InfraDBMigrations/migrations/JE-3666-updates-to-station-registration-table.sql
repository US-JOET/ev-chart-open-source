use evchart_data_v3;

-- renaming misspelled col
alter table station_registrations rename column CMAC to CMAQ;
alter table station_registrations rename column EVCRAA to EVC_RAA;
-- adding new col
alter table station_registrations add column AFC BOOLEAN NOT NULL; 
alter table station_registrations add column num_fed_funded_ports INTEGER; 
alter table station_registrations add column num_non_fed_funded_ports INTEGER; 