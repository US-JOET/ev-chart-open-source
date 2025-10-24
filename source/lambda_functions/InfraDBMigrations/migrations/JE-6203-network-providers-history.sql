USE evchart_data_v3;
CREATE TABLE network_providers_history (
  action_type enum('DELETE','UPDATE','INSERT') DEFAULT NULL,
  changed_data json DEFAULT NULL,
  np_uuid varchar(36) NOT NULL,
  id int NOT NULL AUTO_INCREMENT,
  updated_on datetime DEFAULT NULL,
  updated_by varchar(72) DEFAULT NULL,
  PRIMARY KEY (id)
);