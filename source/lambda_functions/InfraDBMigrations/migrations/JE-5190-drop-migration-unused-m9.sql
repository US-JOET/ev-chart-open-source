USE evchart_data_v3;
DROP TABLE IF EXISTS mig_import_metadata;
DROP TABLE IF EXISTS mig_module2_data_v2;
DROP TABLE IF EXISTS mig_module3_data_v2;
DROP TABLE IF EXISTS mig_module4_data_v2;
DROP TABLE IF EXISTS mig_module5_data_v2;
DROP TABLE IF EXISTS mig_module6_data_v2;
DROP TABLE IF EXISTS mig_module7_data_v2;
DROP TABLE IF EXISTS mig_module8_data_v2;
DROP TABLE IF EXISTS mig_module9_data_v2;
DROP TABLE IF EXISTS mig_registered_stations_v2;

ALTER TABLE module9_data_v3
  DROP COLUMN distribution_cost_federal,
  DROP COLUMN distribution_cost_total,
  DROP COLUMN system_cost_federal,
  DROP system_cost_total;