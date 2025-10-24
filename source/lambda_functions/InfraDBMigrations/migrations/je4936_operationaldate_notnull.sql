-- updating operational_date to be NOT NULL
USE evchart_data_v3;
ALTER TABLE station_registrations MODIFY COLUMN operational_date DATE NOT NULL