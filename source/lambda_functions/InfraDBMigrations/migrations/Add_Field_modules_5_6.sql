-- Adding new fields

-- module 5: add notes
alter table module5_data_v3 add column maintenance_notes  varchar(255); 

-- module 6: add operator_type, notes
alter table module6_data_v3 add column operator_type varchar(255); 
alter table module6_data_v3 add column operator_notes varchar(255); 
