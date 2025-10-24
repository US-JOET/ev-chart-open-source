
-- modules 2,3,4: remove port_id
alter table evchart_data_v3.module2_data_v3 drop column port_id; 
alter table evchart_data_v3.module3_data_v3 drop column port_id;
alter table evchart_data_v3.module4_data_v3 drop column port_id; 