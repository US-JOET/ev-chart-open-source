-- updating outage_duration to be NULL
USE evchart_data_v3;
ALTER TABLE module4_data_v3 MODIFY COLUMN outage_duration DECIMAL(8,2) NULL