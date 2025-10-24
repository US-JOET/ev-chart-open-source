-- Updating the current network providers in the station_registrations table and module tables in the prod database to correctly reflect db_values agreed upon in APIGetNetworkProviders
SET SQL_SAFE_UPDATES = 0; 
USE evchart_data_v3;
-- updating network providers for station_registration tables
UPDATE station_registrations SET network_provider = "chargepoint" WHERE network_provider = "chargepoint_network";
UPDATE station_registrations SET network_provider = "tesla_supercharger" WHERE network_provider = "Tesla Supercharger";
UPDATE station_registrations SET network_provider = "electrify_america" WHERE network_provider = "Electrify America";
UPDATE station_registrations SET network_provider = "evgo" WHERE network_provider = "evgo_network" or network_provider = "EVgo";
UPDATE station_registrations SET network_provider = "red_e_charging" WHERE network_provider = "red_e";
UPDATE station_registrations SET network_provider = "francis_energy" WHERE network_provider = "fcn";

-- updating network providers for module 2 table
UPDATE module2_data_v3 m2 SET m2.network_provider_upload = "chargepoint" WHERE network_provider_upload = "chargepoint_network";
UPDATE module2_data_v3 m2 SET m2.network_provider_upload = "tesla_supercharger" WHERE network_provider_upload = "Tesla Supercharger";
UPDATE module2_data_v3 m2 SET m2.network_provider_upload = "electrify_america" WHERE network_provider_upload = "Electrify America";
UPDATE module2_data_v3 m2 SET m2.network_provider_upload = "evgo" WHERE network_provider_upload = "evgo_network" or network_provider_upload = "EVgo";
UPDATE module2_data_v3 m2 SET m2.network_provider_upload = "red_e_charging" WHERE network_provider_upload = "red_e";
UPDATE module2_data_v3 m2 SET m2.network_provider_upload = "francis_energy" WHERE network_provider_upload = "fcn";

-- updating network providers for module 3 table
UPDATE module3_data_v3 m3 SET m3.network_provider_upload = "chargepoint" WHERE network_provider_upload = "chargepoint_network";
UPDATE module3_data_v3 m3 SET m3.network_provider_upload = "tesla_supercharger" WHERE network_provider_upload = "Tesla Supercharger";
UPDATE module3_data_v3 m3 SET m3.network_provider_upload = "electrify_america" WHERE network_provider_upload = "Electrify America";
UPDATE module3_data_v3 m3 SET m3.network_provider_upload = "evgo" WHERE network_provider_upload = "evgo_network" or network_provider_upload = "EVgo";
UPDATE module3_data_v3 m3 SET m3.network_provider_upload = "red_e_charging" WHERE network_provider_upload = "red_e";
UPDATE module3_data_v3 m3 SET m3.network_provider_upload = "francis_energy" WHERE network_provider_upload = "fcn";

-- updating network providers for module 4 table
UPDATE module4_data_v3 m4 SET m4.network_provider_upload = "chargepoint" WHERE network_provider_upload = "chargepoint_network";
UPDATE module4_data_v3 m4 SET m4.network_provider_upload = "tesla_supercharger" WHERE network_provider_upload = "Tesla Supercharger";
UPDATE module4_data_v3 m4 SET m4.network_provider_upload = "electrify_america" WHERE network_provider_upload = "Electrify America";
UPDATE module4_data_v3 m4 SET m4.network_provider_upload = "evgo" WHERE network_provider_upload = "evgo_network" or network_provider_upload = "EVgo";
UPDATE module4_data_v3 m4 SET m4.network_provider_upload = "red_e_charging" WHERE network_provider_upload = "red_e";
UPDATE module4_data_v3 m4 SET m4.network_provider_upload = "francis_energy" WHERE network_provider_upload = "fcn";

-- updating network providers for module 5 table
UPDATE module5_data_v3 m5 SET m5.network_provider_upload = "chargepoint" WHERE network_provider_upload = "chargepoint_network";
UPDATE module5_data_v3 m5 SET m5.network_provider_upload = "tesla_supercharger" WHERE network_provider_upload = "Tesla Supercharger";
UPDATE module5_data_v3 m5 SET m5.network_provider_upload = "electrify_america" WHERE network_provider_upload = "Electrify America";
UPDATE module5_data_v3 m5 SET m5.network_provider_upload = "evgo" WHERE network_provider_upload = "evgo_network" or network_provider_upload = "EVgo";
UPDATE module5_data_v3 m5 SET m5.network_provider_upload = "red_e_charging" WHERE network_provider_upload = "red_e";
UPDATE module5_data_v3 m5 SET m5.network_provider_upload = "francis_energy" WHERE network_provider_upload = "fcn";

-- updating network providers for module 6 table
UPDATE module6_data_v3 m6 SET m6.network_provider_upload = "chargepoint" WHERE network_provider_upload = "chargepoint_network";
UPDATE module6_data_v3 m6 SET m6.network_provider_upload = "tesla_supercharger" WHERE network_provider_upload = "Tesla Supercharger";
UPDATE module6_data_v3 m6 SET m6.network_provider_upload = "electrify_america" WHERE network_provider_upload = "Electrify America";
UPDATE module6_data_v3 m6 SET m6.network_provider_upload = "evgo" WHERE network_provider_upload = "evgo_network" or network_provider_upload = "EVgo";
UPDATE module6_data_v3 m6 SET m6.network_provider_upload = "red_e_charging" WHERE network_provider_upload = "red_e";
UPDATE module6_data_v3 m6 SET m6.network_provider_upload = "francis_energy" WHERE network_provider_upload = "fcn";

-- updating network providers for module 7 table
UPDATE module7_data_v3 m7 SET m7.network_provider_upload = "chargepoint" WHERE network_provider_upload = "chargepoint_network";
UPDATE module7_data_v3 m7 SET m7.network_provider_upload = "tesla_supercharger" WHERE network_provider_upload = "Tesla Supercharger";
UPDATE module7_data_v3 m7 SET m7.network_provider_upload = "electrify_america" WHERE network_provider_upload = "Electrify America";
UPDATE module7_data_v3 m7 SET m7.network_provider_upload = "evgo" WHERE network_provider_upload = "evgo_network" or network_provider_upload = "EVgo";
UPDATE module7_data_v3 m7 SET m7.network_provider_upload = "red_e_charging" WHERE network_provider_upload = "red_e";
UPDATE module7_data_v3 m7 SET m7.network_provider_upload = "francis_energy" WHERE network_provider_upload = "fcn";

-- updating network providers for module 8 table
UPDATE module8_data_v3 m8 SET m8.network_provider_upload = "chargepoint" WHERE network_provider_upload = "chargepoint_network";
UPDATE module8_data_v3 m8 SET m8.network_provider_upload = "tesla_supercharger" WHERE network_provider_upload = "Tesla Supercharger";
UPDATE module8_data_v3 m8 SET m8.network_provider_upload = "electrify_america" WHERE network_provider_upload = "Electrify America";
UPDATE module8_data_v3 m8 SET m8.network_provider_upload = "evgo" WHERE network_provider_upload = "evgo_network" or network_provider_upload = "EVgo";
UPDATE module8_data_v3 m8 SET m8.network_provider_upload = "red_e_charging" WHERE network_provider_upload = "red_e";
UPDATE module8_data_v3 m8 SET m8.network_provider_upload = "francis_energy" WHERE network_provider_upload = "fcn";

-- updating network providers for module 9 table
UPDATE module9_data_v3 m9 SET m9.network_provider_upload = "chargepoint" WHERE network_provider_upload = "chargepoint_network";
UPDATE module9_data_v3 m9 SET m9.network_provider_upload = "tesla_supercharger" WHERE network_provider_upload = "Tesla Supercharger";
UPDATE module9_data_v3 m9 SET m9.network_provider_upload = "electrify_america" WHERE network_provider_upload = "Electrify America";
UPDATE module9_data_v3 m9 SET m9.network_provider_upload = "evgo" WHERE network_provider_upload = "evgo_network" or network_provider_upload = "EVgo";
UPDATE module9_data_v3 m9 SET m9.network_provider_upload = "red_e_charging" WHERE network_provider_upload = "red_e";
UPDATE module9_data_v3 m9 SET m9.network_provider_upload = "francis_energy" WHERE network_provider_upload = "fcn";