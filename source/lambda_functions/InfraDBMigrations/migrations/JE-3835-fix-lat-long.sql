-- swap defined schema for longitude and latitude for stations
use evchart_data_v3;
ALTER TABLE station_registrations MODIFY latitude decimal(10,8);
ALTER TABLE station_registrations MODIFY longitude decimal(11,8);
