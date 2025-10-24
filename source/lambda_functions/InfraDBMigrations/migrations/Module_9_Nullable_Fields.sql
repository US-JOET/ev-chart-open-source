-- updating module 9 fields to be NULL

ALTER TABLE evchart_data_v3.module9_data_v3 MODIFY COLUMN real_property_cost_total DECIMAL(11,2) NULL;
ALTER TABLE evchart_data_v3.module9_data_v3 MODIFY COLUMN equipment_cost_total DECIMAL(11,2) NULL;
ALTER TABLE evchart_data_v3.module9_data_v3 MODIFY COLUMN equipment_install_cost_total DECIMAL(11,2) NULL;
ALTER TABLE evchart_data_v3.module9_data_v3 MODIFY COLUMN equipment_install_cost_elec DECIMAL(11,2) NULL;
ALTER TABLE evchart_data_v3.module9_data_v3 MODIFY COLUMN equipment_install_cost_const DECIMAL(11,2) NULL;
ALTER TABLE evchart_data_v3.module9_data_v3 MODIFY COLUMN equipment_install_cost_labor DECIMAL(11,2) NULL;
ALTER TABLE evchart_data_v3.module9_data_v3 MODIFY COLUMN equipment_install_cost_other DECIMAL(11,2) NULL;
ALTER TABLE evchart_data_v3.module9_data_v3 MODIFY COLUMN der_cost_total DECIMAL(11,2) NULL;
ALTER TABLE evchart_data_v3.module9_data_v3 MODIFY COLUMN der_install_cost_total DECIMAL(11,2) NULL;
ALTER TABLE evchart_data_v3.module9_data_v3 MODIFY COLUMN dist_sys_cost_total DECIMAL(11,2) NULL;
ALTER TABLE evchart_data_v3.module9_data_v3 MODIFY COLUMN service_cost_total DECIMAL(11,2) NULL;
ALTER TABLE evchart_data_v3.module9_data_v3 MODIFY COLUMN der_acq_owned BOOLEAN NULL;