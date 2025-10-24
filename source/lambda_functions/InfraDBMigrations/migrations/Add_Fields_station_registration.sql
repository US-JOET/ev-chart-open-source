-- adding new fields to station_registrations table 
use evchart_data_v3;
-- and station operational fields
alter table station_registrations add column operational_date DATE DEFAULT NULL; 
-- and funding type
alter table station_registrations add column NEVI BOOLEAN NOT NULL DEFAULT 0; 
alter table station_registrations add column CFI BOOLEAN NOT NULL DEFAULT 0; 
alter table station_registrations add column EVCRAA BOOLEAN NOT NULL DEFAULT 0; 
alter table station_registrations add column CMAC BOOLEAN NOT NULL DEFAULT 0; 
alter table station_registrations add column CRP BOOLEAN NOT NULL DEFAULT 0; 
alter table station_registrations add column OTHER BOOLEAN NOT NULL DEFAULT 0; 