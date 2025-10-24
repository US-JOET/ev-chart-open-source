-- adding new fields to m9 table
use evchart_data_v3;

-- add new columns
alter table evchart_data_v3.module9_data_v3 add column user_reports_no_data boolean DEFAULT 0;