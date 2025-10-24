USE evchart_data_v3;

ALTER TABLE import_metadata ADD COLUMN last_reviewed_by VARCHAR(36);
ALTER TABLE import_metadata ADD COLUMN next_reviewer VARCHAR(36);
ALTER TABLE import_metadata ADD COLUMN past_reviewers JSON;
