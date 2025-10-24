/*
add network_provider_upload to all module tables
*/

use evchart_data_v3;
alter table module2_data_v3 add column network_provider_upload varchar(30);
alter table module3_data_v3 add column network_provider_upload varchar(30); 
alter table module4_data_v3 add column network_provider_upload varchar(30); 
alter table module5_data_v3 add column network_provider_upload varchar(30); 
alter table module6_data_v3 add column network_provider_upload varchar(30); 
alter table module7_data_v3 add column network_provider_upload varchar(30); 
alter table module8_data_v3 add column network_provider_upload varchar(30); 
alter table module9_data_v3 add column network_provider_upload varchar(30);
