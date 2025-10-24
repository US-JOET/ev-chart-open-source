-- Adding new fields

-- modules 2,3,4: add port_uuid
alter table evchart_data_v3.module2_data_v3 add column port_uuid varchar(36); 
alter table evchart_data_v3.module2_data_v3 add column port_id_upload varchar(36);

alter table evchart_data_v3.module3_data_v3 add column port_uuid varchar(36); 
alter table evchart_data_v3.module3_data_v3 add column port_id_upload varchar(36);

alter table evchart_data_v3.module4_data_v3 add column port_uuid varchar(36); 
alter table evchart_data_v3.module4_data_v3 add column port_id_upload varchar(36);