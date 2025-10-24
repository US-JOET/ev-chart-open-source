USE evchart_data_v3;

ALTER TABLE import_metadata DROP COLUMN last_reviewed_by;
ALTER TABLE import_metadata DROP COLUMN next_reviewer;
ALTER TABLE import_metadata DROP COLUMN past_reviewers;
