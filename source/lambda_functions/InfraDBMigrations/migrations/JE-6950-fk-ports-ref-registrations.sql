-- Update module data to map to assumed correct port IDs based on the module station UUID
UPDATE module2_data_v3 m2, (
	SELECT sr.status "station_status", sp.port_uuid "correct_port_uuid", bad_port_uuid FROM station_ports sp
		JOIN (
			SELECT m2.station_uuid "correct_station_uuid", m2.port_id, port_uuid "bad_port_uuid" FROM module2_data_v3 m2
				JOIN (
					SELECT port_uuid, port_id FROM station_ports sp
						LEFT JOIN station_registrations sr USING (station_uuid)
						WHERE sr.status IS NULL
				) orphaned_sp USING (port_uuid)
		) correct_sp_search USING (port_id)
		LEFT JOIN station_registrations sr ON correct_sp_search.correct_station_uuid = sr.station_uuid
		WHERE correct_sp_search.correct_station_uuid = sp.station_uuid
		GROUP BY bad_port_uuid, correct_port_uuid
	) port_map
    SET m2.port_uuid = port_map.correct_port_uuid
    WHERE m2.port_uuid = port_map.bad_port_uuid
    AND port_map.station_status = 'Active';

UPDATE module3_data_v3 m3, (
	SELECT sr.status "station_status", sp.port_uuid "correct_port_uuid", bad_port_uuid FROM station_ports sp
		JOIN (
			SELECT m3.station_uuid "correct_station_uuid", m3.port_id, port_uuid "bad_port_uuid" FROM module3_data_v3 m3
				JOIN (
					SELECT port_uuid, port_id FROM station_ports sp
						LEFT JOIN station_registrations sr USING (station_uuid)
						WHERE sr.status IS NULL
				) orphaned_sp USING (port_uuid)
		) correct_sp_search USING (port_id)
		LEFT JOIN station_registrations sr ON correct_sp_search.correct_station_uuid = sr.station_uuid
		WHERE correct_sp_search.correct_station_uuid = sp.station_uuid
		GROUP BY bad_port_uuid, correct_port_uuid
	) port_map
    SET m3.port_uuid = port_map.correct_port_uuid
    WHERE m3.port_uuid = port_map.bad_port_uuid
    AND port_map.station_status = 'Active';

UPDATE module4_data_v3 m4, (
	SELECT sr.status "station_status", sp.port_uuid "correct_port_uuid", bad_port_uuid FROM station_ports sp
		JOIN (
			SELECT m4.station_uuid "correct_station_uuid", m4.port_id, port_uuid "bad_port_uuid" FROM module4_data_v3 m4
				JOIN (
					SELECT port_uuid, port_id FROM station_ports sp
						LEFT JOIN station_registrations sr USING (station_uuid)
						WHERE sr.status IS NULL
				) orphaned_sp USING (port_uuid)
		) correct_sp_search USING (port_id)
		LEFT JOIN station_registrations sr ON correct_sp_search.correct_station_uuid = sr.station_uuid
		WHERE correct_sp_search.correct_station_uuid = sp.station_uuid
		GROUP BY bad_port_uuid, correct_port_uuid
	) port_map
    SET m4.port_uuid = port_map.correct_port_uuid
    WHERE m4.port_uuid = port_map.bad_port_uuid
    AND port_map.station_status = 'Active';

-- Delete orphaned ports
DELETE sp FROM station_ports sp
    LEFT JOIN station_registrations sr USING (station_uuid)
    WHERE sr.status IS NULL;

-- Finally, add the foreign key (hopefully without issue)
ALTER TABLE station_ports
    ADD CONSTRAINT fk_station_ports_station_registrations
    FOREIGN KEY (station_uuid)
    REFERENCES station_registrations(station_uuid);
