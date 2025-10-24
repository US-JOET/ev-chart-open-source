-- updating length of the ports field in the station_registrations table as a quick fix for V2.2 release
use evchart_data_v3;
ALTER TABLE station_registrations MODIFY ports VARCHAR(255);