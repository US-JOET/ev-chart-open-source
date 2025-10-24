-- adding new fields to m2, m3, m4 tables
use evchart_data_v3;
-- remove previous column
alter table evchart_data_v3.module2_data_v3 drop column acknowledge_missing_data;
alter table evchart_data_v3.module3_data_v3 drop column acknowledge_missing_data;
alter table evchart_data_v3.module4_data_v3 drop column acknowledge_missing_data;

-- add new columns
alter table evchart_data_v3.module2_data_v3 add column user_reports_no_data boolean DEFAULT 0;
alter table evchart_data_v3.module3_data_v3 add column user_reports_no_data boolean DEFAULT 0;
alter table evchart_data_v3.module4_data_v3 add column user_reports_no_data boolean DEFAULT 0;