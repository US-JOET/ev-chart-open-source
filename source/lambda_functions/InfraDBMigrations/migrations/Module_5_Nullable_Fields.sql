-- updating module 5 field to be NULL

ALTER TABLE evchart_data_v3.module5_data_v3 MODIFY COLUMN maintenance_cost_total DECIMAL(9,2) NULL;