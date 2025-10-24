-- adding new fields to m2, m3, m4 tables
use evchart_data_v3;
-- and acknowledge_missing_data
alter table evchart_data_v3.module2_data_v3 add column acknowledge_missing_data TINYINT(1) DEFAULT 0;

alter table evchart_data_v3.module3_data_v3 add column acknowledge_missing_data TINYINT(1) DEFAULT 0;

alter table evchart_data_v3.module4_data_v3 add column acknowledge_missing_data TINYINT(1) DEFAULT 0;