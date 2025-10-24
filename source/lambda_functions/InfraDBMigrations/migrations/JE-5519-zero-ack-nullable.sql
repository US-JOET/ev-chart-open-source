USE evchart_data_v3;

ALTER TABLE module2_data_v3
    MODIFY session_start DATETIME DEFAULT NULL;
ALTER TABLE module2_data_v3
    MODIFY session_end DATETIME DEFAULT NULL;
ALTER TABLE module2_data_v3
    MODIFY session_error VARCHAR(255) DEFAULT NULL;
ALTER TABLE module2_data_v3
    MODIFY energy_kwh DECIMAL(7,2) DEFAULT NULL;
ALTER TABLE module2_data_v3
    MODIFY power_kw DECIMAL(7,2) DEFAULT NULL;
ALTER TABLE module2_data_v3
    MODIFY payment_method VARCHAR(255) DEFAULT NULL;

ALTER TABLE module3_data_v3
    MODIFY uptime DECIMAL(5,2) DEFAULT NULL;

ALTER TABLE module4_data_v3
    MODIFY outage_duration DECIMAL(8,2) DEFAULT NULL;

ALTER TABLE module5_data_v3
    MODIFY maintenance_cost_total DECIMAL(9,2) DEFAULT NULL;

ALTER TABLE module9_data_v3
    MODIFY real_property_cost_total DECIMAL(11,2) DEFAULT NULL;
ALTER TABLE module9_data_v3
    MODIFY equipment_cost_total DECIMAL(11,2) DEFAULT NULL;
ALTER TABLE module9_data_v3
    MODIFY equipment_install_cost_total DECIMAL(11,2) DEFAULT NULL;
ALTER TABLE module9_data_v3
    MODIFY equipment_install_cost_elec DECIMAL(11,2) DEFAULT NULL;
ALTER TABLE module9_data_v3
    MODIFY equipment_install_cost_const DECIMAL(11,2) DEFAULT NULL;
ALTER TABLE module9_data_v3
    MODIFY equipment_install_cost_labor DECIMAL(11,2) DEFAULT NULL;
ALTER TABLE module9_data_v3
    MODIFY equipment_install_cost_other DECIMAL(11,2) DEFAULT NULL;
ALTER TABLE module9_data_v3
    MODIFY der_acq_owned TINYINT(1) DEFAULT NULL;
ALTER TABLE module9_data_v3
    MODIFY der_cost_total DECIMAL(11,2) DEFAULT NULL;
ALTER TABLE module9_data_v3
    MODIFY der_install_cost_total DECIMAL(11,2) DEFAULT NULL;
ALTER TABLE module9_data_v3
    MODIFY dist_sys_cost_total DECIMAL(11,2) DEFAULT NULL;
ALTER TABLE module9_data_v3
    MODIFY service_cost_total DECIMAL(11,2) DEFAULT NULL;