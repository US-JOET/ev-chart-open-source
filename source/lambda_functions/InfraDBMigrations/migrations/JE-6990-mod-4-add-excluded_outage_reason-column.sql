-- Valid values 1-6 Tiny int is maximum of 127
ALTER TABLE module4_data_v3 
ADD COLUMN excluded_outage_reason TINYINT UNSIGNED DEFAULT NULL,
ADD CONSTRAINT excluded_outage_reason_range CHECK (excluded_outage_reason BETWEEN 1 AND 6);