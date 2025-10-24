use evchart_data_v3;

-- update to m3
ALTER TABLE module3_data_v3 MODIFY total_outage decimal(8, 2);
ALTER TABLE module3_data_v3 MODIFY total_outage_excl decimal(8, 2);

-- adding to module 8
ALTER TABLE module8_data_v3 MODIFY der_kw decimal(10, 2);
ALTER TABLE module8_data_v3 MODIFY der_kwh decimal(10, 2);