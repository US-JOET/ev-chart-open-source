-- updating module 2 session_error to be NULL

ALTER TABLE evchart_data_v3.module2_data_v3 MODIFY COLUMN session_error VARCHAR(255);