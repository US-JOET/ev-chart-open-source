-- updating all data in module 9 to be corrected from “999999999.99” to “NULL”  

UPDATE evchart_data_v3.module9_data_v3
SET real_property_cost_total = NULL
WHERE real_property_cost_total = 999999999.99;

UPDATE evchart_data_v3.module9_data_v3
SET equipment_cost_total = NULL
WHERE equipment_cost_total = 999999999.99;

UPDATE evchart_data_v3.module9_data_v3
SET equipment_install_cost_total = NULL
WHERE equipment_install_cost_total = 999999999.99;

UPDATE evchart_data_v3.module9_data_v3
SET equipment_install_cost_elec = NULL
WHERE equipment_install_cost_elec = 999999999.99;

UPDATE evchart_data_v3.module9_data_v3
SET equipment_install_cost_const = NULL
WHERE equipment_install_cost_const = 999999999.99;

UPDATE evchart_data_v3.module9_data_v3
SET equipment_install_cost_labor = NULL
WHERE equipment_install_cost_labor = 999999999.99;

UPDATE evchart_data_v3.module9_data_v3
SET equipment_install_cost_other = NULL
WHERE equipment_install_cost_other = 999999999.99;

UPDATE evchart_data_v3.module9_data_v3
SET der_cost_total = NULL
WHERE der_cost_total = 999999999.99;

UPDATE evchart_data_v3.module9_data_v3
SET der_install_cost_total = NULL
WHERE der_install_cost_total = 999999999.99;

UPDATE evchart_data_v3.module9_data_v3
SET dist_sys_cost_total = NULL
WHERE dist_sys_cost_total = 999999999.99;

UPDATE evchart_data_v3.module9_data_v3
SET service_cost_total = NULL
WHERE service_cost_total = 999999999.99;