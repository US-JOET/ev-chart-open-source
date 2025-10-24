USE evchart_data_v3;
ALTER TABLE module5_data_v3 MODIFY column project_id VARCHAR(256);

UPDATE module5_data_v3
   SET project_id = "Prepaid O&M Costs - 1 Month Prorate (Pre-paid 5 years). Warranty, Prepaid Maintenance, Service, Networking"
 WHERE project_id = "Prepaid O&M Costs - 1 Month Prorate ";
