-- updating module 2 fields to be NULL

ALTER TABLE evchart_data_v3.module2_data_v3 MODIFY COLUMN session_start DATETIME NULL;
ALTER TABLE evchart_data_v3.module2_data_v3 MODIFY COLUMN session_end DATETIME;
ALTER TABLE evchart_data_v3.module2_data_v3 MODIFY COLUMN energy_kwh DECIMAL(7,2);
ALTER TABLE evchart_data_v3.module2_data_v3 MODIFY COLUMN power_kw DECIMAL(7,2);
ALTER TABLE evchart_data_v3.module2_data_v3 MODIFY COLUMN payment_method VARCHAR(255);