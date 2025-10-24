SET SQL_SAFE_UPDATES = 0;
update evchart_data_v3.module2_data_v3 a
inner join evchart_data_v3.station_registrations b
on a.station_uuid = b.station_uuid
set a.network_provider_upload = b.network_provider;

update evchart_data_v3.module3_data_v3 a
inner join evchart_data_v3.station_registrations b
on a.station_uuid = b.station_uuid
set a.network_provider_upload = b.network_provider;

update evchart_data_v3.module4_data_v3 a
inner join evchart_data_v3.station_registrations b
on a.station_uuid = b.station_uuid
set a.network_provider_upload = b.network_provider;

update evchart_data_v3.module5_data_v3 a
inner join evchart_data_v3.station_registrations b
on a.station_uuid = b.station_uuid
set a.network_provider_upload = b.network_provider;

update evchart_data_v3.module6_data_v3 a
inner join evchart_data_v3.station_registrations b
on a.station_uuid = b.station_uuid
set a.network_provider_upload = b.network_provider;

update evchart_data_v3.module7_data_v3 a
inner join evchart_data_v3.station_registrations b
on a.station_uuid = b.station_uuid
set a.network_provider_upload = b.network_provider;

update evchart_data_v3.module8_data_v3 a
inner join evchart_data_v3.station_registrations b
on a.station_uuid = b.station_uuid
set a.network_provider_upload = b.network_provider;

update evchart_data_v3.module9_data_v3 a
inner join evchart_data_v3.station_registrations b
on a.station_uuid = b.station_uuid
set a.network_provider_upload = b.network_provider;




