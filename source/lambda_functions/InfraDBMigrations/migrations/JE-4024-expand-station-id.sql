USE evchart_data_v3;
ALTER TABLE station_registrations MODIFY column station_id VARCHAR(36);
UPDATE station_registrations
   SET station_id="11e7a34f-88ba-4729-803d-06a5616afd69"
 WHERE station_id="11e7a34f-88ba-4729-803d-06a561";