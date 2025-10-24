-- updating uptime in module 3 to be nullable

ALTER TABLE evchart_data_v3.module3_data_v3 MODIFY COLUMN uptime DECIMAL(5,2) NULL;
