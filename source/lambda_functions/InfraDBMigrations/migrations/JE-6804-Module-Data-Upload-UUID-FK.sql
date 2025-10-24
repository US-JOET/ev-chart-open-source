USE evchart_data_v3;

-- ALTER TABLE module2_data_v3
--     ADD CONSTRAINT fk_upload_id_m2
--     FOREIGN KEY (upload_id)
--     REFERENCES import_metadata(upload_id);
--
-- ALTER TABLE module3_data_v3
--     ADD CONSTRAINT fk_upload_id_m3
--     FOREIGN KEY (upload_id)
--     REFERENCES import_metadata(upload_id);
--
-- ALTER TABLE module4_data_v3
--     ADD CONSTRAINT fk_upload_id_m4
--     FOREIGN KEY (upload_id)
--     REFERENCES import_metadata(upload_id);

-- Orphaned module data.
DELETE FROM module5_data_v3
    WHERE upload_id = 'b01d4568-f3a7-4ae6-a7ef-47c4cf2ce3cb';

-- Orphaned module data.
DELETE FROM module8_data_v3
    WHERE upload_id = '5eb0bfe1-db6b-4bf2-aa20-b3b80150b485';

ALTER TABLE module5_data_v3
    ADD CONSTRAINT fk_upload_id_m5
    FOREIGN KEY (upload_id)
    REFERENCES import_metadata(upload_id);

ALTER TABLE module6_data_v3
    ADD CONSTRAINT fk_upload_id_m6
    FOREIGN KEY (upload_id)
    REFERENCES import_metadata(upload_id);

ALTER TABLE module7_data_v3
    ADD CONSTRAINT fk_upload_id_m7
    FOREIGN KEY (upload_id)
    REFERENCES import_metadata(upload_id);

ALTER TABLE module8_data_v3
    ADD CONSTRAINT fk_upload_id_m8
    FOREIGN KEY (upload_id)
    REFERENCES import_metadata(upload_id);

ALTER TABLE module9_data_v3
    ADD CONSTRAINT fk_upload_id_m9
    FOREIGN KEY (upload_id)
    REFERENCES import_metadata(upload_id);
