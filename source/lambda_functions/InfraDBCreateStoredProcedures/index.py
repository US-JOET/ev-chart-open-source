"""
InfraDBCreateStoredProcedures

Defines and creates the MySQL stored procedures as part of the application deployment process.
"""
from itertools import chain
import pymysql
from evchart_helper import aurora

ev_submission_summary = [
    """
        drop procedure if exists evchart_data_v3.ev_chart_download_tracker;
    """
]

ev_chart_download_modules = [
    """
        use evchart_data_v3
    """,
    """
        drop procedure if exists ev_chart_download_modules;
    """,
    """
    CREATE procedure ev_chart_download_modules(
        IN
        module_list VARCHAR(255),
        rpt_year VARCHAR(255),
        rpt_quarter VARCHAR(255),
        rpt_network_provider VARCHAR(10240),
        rpt_st_id  VARCHAR(10240),
        rpt_dr_id  VARCHAR(10240),
        rpt_sr_id  VARCHAR(10240)
    )
    BEGIN
        DECLARE done INT DEFAULT 0;
        DECLARE pos INT DEFAULT 1;
        DECLARE modulename VARCHAR(50);
        DECLARE delim_pos INT;
        DECLARE column_list VARCHAR(1024);
        DECLARE dr_selected BOOLEAN DEFAULT TRUE;
        DECLARE sr_selected BOOLEAN DEFAULT TRUE;
        DECLARE CONTINUE HANDLER FOR SQLSTATE '02000' SET done = 1;
        IF module_list = -1 THEN
            SET module_list = "station_registrations,module2_data_v3,module3_data_v3,module4_data_v3,module5_data_v3,module6_data_v3,module7_data_v3,module8_data_v3,module9_data_v3";
        END IF;
        IF rpt_quarter = -1 THEN
            SET rpt_quarter = "'1','2','3','4'";
        END IF;
        IF rpt_year = -1 THEN
            set rpt_year = "SELECT DISTINCT year FROM import_metadata";
        END IF;
        IF rpt_network_provider = -1 THEN
            set rpt_network_provider = "SELECT DISTINCT network_provider FROM(
            SELECT DISTINCT network_provider
            FROM station_registrations
            UNION
            SELECT DISTINCT network_provider_upload
            FROM module2_data_v3
            UNION
            SELECT DISTINCT network_provider_upload
            FROM module3_data_v3
            UNION
            SELECT DISTINCT network_provider_upload
            FROM module4_data_v3
            UNION
            SELECT DISTINCT network_provider_upload
            FROM module5_data_v3
            UNION
            SELECT DISTINCT network_provider_upload
            FROM module6_data_v3
            UNION
            SELECT DISTINCT network_provider_upload
            FROM module7_data_v3
            UNION
            SELECT DISTINCT network_provider_upload
            FROM module8_data_v3
            UNION
            SELECT DISTINCT network_provider_upload
            FROM module9_data_v3
        ) AS network_provider";
        END IF;
        IF rpt_st_id = -1 THEN
            set rpt_st_id = "SELECT DISTINCT station_uuid FROM station_registrations";
        END IF;
        IF rpt_dr_id = -1 THEN
            set rpt_dr_id = "SELECT parent_org FROM import_metadata UNION SELECT dr_id FROM station_registrations";
            set dr_selected = FALSE;
        END IF;
        IF rpt_sr_id = -1 THEN
            set rpt_sr_id = "SELECT DISTINCT sr_id FROM station_authorizations";
            set sr_selected = FALSE;
        END IF;
        loop_through_csv: LOOP
            SET delim_pos = LOCATE(',', module_list, pos);
            IF delim_pos = 0 THEN
                SET modulename = SUBSTRING(module_list, pos);
                SET done = 1;
            ELSE
                SET modulename = SUBSTRING(module_list, pos, delim_pos - pos);
                SET pos = delim_pos + 1;
            END IF;
            SET @table_name = modulename;
            SELECT
            GROUP_CONCAT('md.',column_name SEPARATOR ',') INTO column_list
            FROM
            information_schema.columns
            WHERE
            table_name = @table_name
            AND table_schema = 'evchart_data_v3';
            SET @getstation_to_csv_dr_or_default = CONCAT(
                "SELECT '", modulename, "' AS module, ", column_list,
                " FROM ", @table_name, " md ",
                "WHERE network_provider IN (", rpt_network_provider, ") AND md.station_uuid IN (",rpt_st_id,") AND dr_id IN (",rpt_dr_id,") AND md.status = 'Active'"
                );
            SET @getstation_to_csv_sr_selected = CONCAT(
                "SELECT '", modulename, "' AS module, sa.sr_id, ", column_list,
                " FROM ", @table_name, " md ",
                "INNER JOIN station_authorizations sa ON (sa.station_uuid = md.station_uuid and sa.dr_id = md.dr_id)",
                "WHERE md.network_provider IN (", rpt_network_provider, ") AND sa.station_uuid IN (",rpt_st_id,") AND sa.dr_id IN (",rpt_dr_id,") AND sa.sr_id IN (",rpt_sr_id,") AND md.status = 'Active'"
                );
            SET @getannual_to_csv_dr_or_default = CONCAT(
                "SELECT '", modulename, "' AS module, im.parent_org AS dr_id, im.org_id AS sr_id,", column_list,
                " FROM ", @table_name, " md ",
                "INNER JOIN import_metadata im ON md.upload_id = im.upload_id ",
                "WHERE year IN (", rpt_year, ") AND network_provider_upload IN (", rpt_network_provider, ") AND md.station_uuid IN (",rpt_st_id,") AND im.parent_org IN (",rpt_dr_id,") AND (im.submission_status = 'Submitted' OR im.submission_status = 'Approved')"
            );
            SET @getannual_to_csv_sr_selected = CONCAT(
                "SELECT '", modulename, "' AS module, im.parent_org AS dr_id, im.org_id AS sr_id,", column_list,
                " FROM ", @table_name, " md ",
                "INNER JOIN import_metadata im ON md.upload_id = im.upload_id ",
                "WHERE year IN (", rpt_year, ") AND network_provider_upload IN (", rpt_network_provider, ") AND md.station_uuid IN (",rpt_st_id,") AND im.parent_org IN (",rpt_dr_id,") AND im.org_id IN (",rpt_sr_id,") AND im.submission_status='Approved'"
            );
            SET @getquarter_to_csv_dr_or_default = CONCAT(
                "SELECT '", modulename, "' AS module, im.parent_org AS dr_id, im.org_id AS sr_id,year,quarter,", column_list,
                " FROM ", @table_name, " md ",
                "INNER JOIN import_metadata im ON md.upload_id = im.upload_id ",
                "WHERE quarter IN (", rpt_quarter, ") AND year IN (", rpt_year, ") AND network_provider_upload IN (", rpt_network_provider, ") AND md.station_uuid IN (",rpt_st_id,") AND im.parent_org IN (",rpt_dr_id,") AND (im.submission_status = 'Submitted' OR im.submission_status = 'Approved')"
            );
            SET @getquarter_to_csv_sr_selected = CONCAT(
                "SELECT '", modulename, "' AS module, im.parent_org AS dr_id, im.org_id AS sr_id,", column_list,
                " FROM ", @table_name, " md ",
                "INNER JOIN import_metadata im ON md.upload_id = im.upload_id ",
                "WHERE quarter IN (", rpt_quarter, ") AND year IN (", rpt_year, ") AND network_provider_upload IN (", rpt_network_provider, ") AND md.station_uuid IN (",rpt_st_id,") AND im.parent_org IN (",rpt_dr_id,") AND im.org_id IN (",rpt_sr_id,") AND im.submission_status='Approved'"
            );
            SET @getonce_to_csv_dr_or_default = CONCAT(
            "SELECT '", modulename, "' AS module, im.parent_org AS dr_id, im.org_id AS sr_id,", column_list,
            " FROM ", @table_name, " md ",
            "INNER JOIN import_metadata im ON md.upload_id = im.upload_id ",
            "WHERE md.station_uuid IN (",rpt_st_id,") AND md.network_provider_upload IN (", rpt_network_provider, ") AND im.parent_org IN (",rpt_dr_id,")  AND (im.submission_status = 'Submitted' OR im.submission_status = 'Approved')"
            );

            SET @getonce_to_csv_sr_selected = CONCAT(
                "SELECT '", modulename, "' AS module, im.parent_org AS dr_id, im.org_id AS sr_id,", column_list,
                " FROM ", @table_name, " md ",
                "inner join import_metadata im on md.upload_id = im.upload_id " ,
                "where md.station_uuid in (",rpt_st_id,") and network_provider_upload in (", rpt_network_provider, ") and im.parent_org in (",rpt_dr_id,") and im.org_id in (",rpt_sr_id,") and im.submission_status='Approved'"
            );
            SET @getonce_to_csv_dr_sr = CONCAT(
                    "SELECT '", modulename, "' as module, sa.dr_id,sa.sr_id,", column_list,
                " FROM ", @table_name, " md ",
                "inner join import_metadata im on md.upload_id = im.upload_id ",
                "inner join station_authorizations sa on md.station_uuid = sa.station_uuid ",
                "where sa.station_uuid in (",rpt_st_id,") and network_provider_upload in (", rpt_network_provider, ") and dr_id in (",rpt_dr_id,") and sr_id in (",rpt_sr_id,") and im.submission_status='Approved'"
            );
            IF modulename in ('station_registrations') THEN
                IF sr_selected = TRUE THEN
                    PREPARE stmt FROM @getstation_to_csv_sr_selected;
                ELSE
                    PREPARE stmt FROM @getstation_to_csv_dr_or_default;
                END IF;
            END IF;
            IF modulename in ('module5_data_v3','module7_data_v3') THEN
                IF sr_selected = TRUE THEN
                    PREPARE stmt FROM @getannual_to_csv_sr_selected;
                ELSE
                    PREPARE stmt FROM @getannual_to_csv_dr_or_default;
                END IF;
            END IF;
            IF modulename in ('module6_data_v3','module8_data_v3','module9_data_v3') THEN
                IF sr_selected = TRUE THEN
                    PREPARE stmt FROM @getonce_to_csv_sr_selected;
                ELSE
                    PREPARE stmt FROM @getonce_to_csv_dr_or_default;
                END IF;
            END IF;
            IF modulename in ('module2_data_v3','module3_data_v3','module4_data_v3') THEN
                IF sr_selected = TRUE THEN
                    PREPARE stmt FROM  @getquarter_to_csv_sr_selected;
                ELSE
                    PREPARE stmt FROM@getquarter_to_csv_dr_or_default;
                END IF;
            END IF;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;
            IF done THEN
                LEAVE loop_through_csv;
            END IF;
        END LOOP;
    END
    """
]

ev_chart_populate_port_table = [
    """
       use evchart_data_v3;
    """,
    """
        drop procedure if exists parse_ports_list;
    """,
    """
    CREATE PROCEDURE parse_ports_list(
      IN s_uuid VARCHAR(255), IN port_list VARCHAR(255)
    )
        BEGIN
            DECLARE port_name VARCHAR(255);
            DECLARE pos INT DEFAULT 1;

            WHILE pos > 0 DO
                SET pos = INSTR(port_list, ',');
                IF pos > 0 THEN
                    SET port_name = TRIM(SUBSTRING(port_list, 1, pos-1));
                    SET port_list = SUBSTRING(port_list, pos + 1);
                ELSE
                    SET port_name = TRIM(port_list);
                END IF;
                INSERT INTO station_ports (port_uuid,port_id,station_uuid)
                VALUES (uuid(),port_name,s_uuid);

            END WHILE;
        END;
    """,
    """
        drop procedure if exists populate_port_table;
    """,
    """
        CREATE PROCEDURE populate_port_table()
        BEGIN
            DECLARE i INT DEFAULT 0;
            DECLARE n INT;
            DECLARE s_uuid VARCHAR(255);
            DECLARE ports_list VARCHAR(255);

            SELECT COUNT(*) INTO n FROM station_registrations
             WHERE LENGTH(ports) > 0;

            WHILE i  < n DO
                SELECT station_uuid, ports INTO s_uuid, ports_list
                FROM station_registrations WHERE LENGTH(ports) > 0 LIMIT i, 1;
                CALL parse_ports_list(s_uuid, ports_list);
                SET i = i + 1;
            END WHILE;
        END;
    """
]

ev_chart_update_station_uuids = [
    "drop procedure if exists evchart_data_v3.update_station_uuids;",
    """
    CREATE PROCEDURE update_station_uuids(
      IN old_uuid_list VARCHAR(10240), IN new_uuid_list VARCHAR(10240)
    )
    BEGIN
        DECLARE pos INTEGER DEFAULT 1;
        DECLARE new_pos INTEGER DEFAULT 1;
        DECLARE old_uuid VARCHAR(255);
        DECLARE new_uuid VARCHAR(255);

        WHILE pos > 0 DO
            SET pos = INSTR(old_uuid_list, ",");
            SET new_pos = INSTR(new_uuid_list, ",");

            IF pos > 0 THEN
                SET old_uuid = TRIM(SUBSTRING(old_uuid_list, 1, pos-1));
                SET old_uuid_list = SUBSTRING(old_uuid_list, pos + 1);
            ELSE
                SET old_uuid = TRIM(old_uuid_list);
            END IF;

            IF new_pos > 0 THEN
                SET new_uuid = TRIM(SUBSTRING(new_uuid_list, 1, new_pos-1));
                SET new_uuid_list = SUBSTRING(new_uuid_list, new_pos + 1);
            ELSE
                SET new_uuid = TRIM(new_uuid_list);
            END IF;

            UPDATE station_registrations sr SET sr.station_uuid = new_uuid
             WHERE sr.station_uuid = old_uuid;
            UPDATE station_ports sp SET sp.station_uuid = new_uuid
             WHERE sp.station_uuid = old_uuid;
            UPDATE station_authorizations sa SET sa.station_uuid = new_uuid
             WHERE sa.station_uuid = old_uuid;
            UPDATE module2_data_v3 m2 SET m2.station_uuid = new_uuid
             WHERE m2.station_uuid = old_uuid;
            UPDATE module3_data_v3 m3 SET m3.station_uuid = new_uuid
             WHERE m3.station_uuid = old_uuid;
            UPDATE module4_data_v3 m4 SET m4.station_uuid = new_uuid
             WHERE m4.station_uuid = old_uuid;
            UPDATE module5_data_v3 m5 SET m5.station_uuid = new_uuid
             WHERE m5.station_uuid = old_uuid;
            UPDATE module6_data_v3 m6 SET m6.station_uuid = new_uuid
             WHERE m6.station_uuid = old_uuid;
            UPDATE module7_data_v3 m7 SET m7.station_uuid = new_uuid
             WHERE m7.station_uuid = old_uuid;
            UPDATE module8_data_v3 m8 SET m8.station_uuid = new_uuid
             WHERE m8.station_uuid = old_uuid;
            UPDATE module9_data_v3 m9 SET m9.station_uuid = new_uuid
             WHERE m9.station_uuid = old_uuid;

        END WHILE;

    END;
    """
]

ev_chart_download_modules2 = [
     """
        use evchart_data_v3
    """,
    """
        drop procedure if exists ev_chart_download_modules2;
    """,
    """
    CREATE PROCEDURE ev_chart_download_modules2(
	IN
	module_list VARCHAR(255),
	rpt_year VARCHAR(255),
	rpt_quarter VARCHAR(255),
	rpt_network_provider VARCHAR(10240),
	rpt_st_id  VARCHAR(10240),
	rpt_dr_id  VARCHAR(10240),
	rpt_sr_id  VARCHAR(10240)
)
BEGIN
		DECLARE done INT DEFAULT 0;
		DECLARE pos INT DEFAULT 1;
		DECLARE modulename VARCHAR(50);
		DECLARE delim_pos INT;
		DECLARE column_list VARCHAR(1024);
		DECLARE dr_selected BOOLEAN DEFAULT TRUE;
		DECLARE sr_selected BOOLEAN DEFAULT TRUE;
		DECLARE CONTINUE HANDLER FOR SQLSTATE '02000' SET done = 1;
		IF module_list = -1 THEN
			SET module_list = "station_registrations,module2_data_v3,module3_data_v3,module4_data_v3,module5_data_v3,module6_data_v3,module7_data_v3,module8_data_v3,module9_data_v3";
		END IF;
		IF rpt_quarter = -1 THEN
			SET rpt_quarter = "'1','2','3','4'";
		END IF;
		IF rpt_year = -1 THEN
			set rpt_year = "SELECT DISTINCT year FROM import_metadata";
		END IF;
		IF rpt_network_provider = -1 THEN
			set rpt_network_provider = "SELECT DISTINCT network_provider FROM(
			SELECT DISTINCT network_provider
			FROM station_registrations
			UNION
			SELECT DISTINCT network_provider_upload
			FROM module2_data_v3
			UNION
			SELECT DISTINCT network_provider_upload
			FROM module3_data_v3
			UNION
			SELECT DISTINCT network_provider_upload
			FROM module4_data_v3
			UNION
			SELECT DISTINCT network_provider_upload
			FROM module5_data_v3
			UNION
			SELECT DISTINCT network_provider_upload
			FROM module6_data_v3
			UNION
			SELECT DISTINCT network_provider_upload
			FROM module7_data_v3
			UNION
			SELECT DISTINCT network_provider_upload
			FROM module8_data_v3
			UNION
			SELECT DISTINCT network_provider_upload
			FROM module9_data_v3
		) AS network_provider";
		END IF;
		IF rpt_st_id = -1 THEN
			set rpt_st_id = "SELECT DISTINCT station_uuid FROM station_registrations";
		END IF;
		IF rpt_dr_id = -1 THEN
			set rpt_dr_id = "SELECT parent_org FROM import_metadata UNION SELECT dr_id FROM station_registrations";
			set dr_selected = FALSE;
		END IF;
		IF rpt_sr_id = -1 THEN
			set rpt_sr_id = "SELECT DISTINCT sr_id FROM station_authorizations";
			set sr_selected = FALSE;
		END IF;
		loop_through_csv: LOOP
			SET delim_pos = LOCATE(',', module_list, pos);
			IF delim_pos = 0 THEN
				SET modulename = SUBSTRING(module_list, pos);
				SET done = 1;
			ELSE
				SET modulename = SUBSTRING(module_list, pos, delim_pos - pos);
				SET pos = delim_pos + 1;
			END IF;
			SET @table_name = modulename;
			SELECT
			GROUP_CONCAT('md.',column_name SEPARATOR ',') INTO column_list
			FROM
			information_schema.columns
			WHERE
			table_name = @table_name
			AND table_schema = 'evchart_data_v3';
			SET @getstation_to_csv_dr_or_default = CONCAT(
				"SELECT '", modulename, "' AS module, np.network_provider_value,", column_list,
				" FROM ", @table_name, " md ",
				" INNER JOIN station_registrations sr on sr.station_uuid = md.station_uuid ",
				" INNER JOIN network_providers np on sr.network_provider_uuid = np.network_provider_uuid ",
				"WHERE md.network_provider IN (", rpt_network_provider, ") AND md.station_uuid IN (",rpt_st_id,") AND sr.dr_id IN (",rpt_dr_id,") AND md.status = 'Active'"
				);
			SET @getstation_to_csv_sr_selected = CONCAT(
				"SELECT '", modulename, "' AS module, sa.sr_id, np.network_provider_value,", column_list,
				" FROM ", @table_name, " md ",
				" INNER JOIN station_registrations sr on sr.station_uuid = md.station_uuid ",
				" INNER JOIN network_providers np on sr.network_provider_uuid = np.network_provider_uuid ",
				"INNER JOIN station_authorizations sa ON (sa.station_uuid = md.station_uuid and sa.dr_id = md.dr_id)",
				"WHERE md.network_provider IN (", rpt_network_provider, ") AND sa.station_uuid IN (",rpt_st_id,") AND sa.dr_id IN (",rpt_dr_id,") AND sa.sr_id IN (",rpt_sr_id,") AND md.status = 'Active'"
				);
			SET @getannual_to_csv_dr_or_default = CONCAT(
				"SELECT '", modulename, "' AS module, im.parent_org AS dr_id, im.org_id AS sr_id, np.network_provider_value,", column_list,
				" FROM ", @table_name, " md ",
				" INNER JOIN station_registrations sr on sr.station_uuid = md.station_uuid ",
				" INNER JOIN network_providers np on sr.network_provider_uuid = np.network_provider_uuid ",
				"INNER JOIN import_metadata im ON md.upload_id = im.upload_id ",
				"WHERE year IN (", rpt_year, ") AND network_provider_upload IN (", rpt_network_provider, ") AND md.station_uuid IN (",rpt_st_id,") AND im.parent_org IN (",rpt_dr_id,") AND (im.submission_status = 'Submitted' OR im.submission_status = 'Approved')"
			);
			SET @getannual_to_csv_sr_selected = CONCAT(
				"SELECT '", modulename, "' AS module, im.parent_org AS dr_id, im.org_id AS sr_id, np.network_provider_value,", column_list,
				" FROM ", @table_name, " md ",
				"INNER JOIN import_metadata im ON md.upload_id = im.upload_id ",
				" INNER JOIN station_registrations sr on sr.station_uuid = md.station_uuid ",
				" INNER JOIN network_providers np on sr.network_provider_uuid = np.network_provider_uuid ",
				"WHERE year IN (", rpt_year, ") AND network_provider_upload IN (", rpt_network_provider, ") AND md.station_uuid IN (",rpt_st_id,") AND im.parent_org IN (",rpt_dr_id,") AND im.org_id IN (",rpt_sr_id,") AND im.submission_status='Approved'"
			);
			SET @getquarter_to_csv_dr_or_default = CONCAT(
				"SELECT '", modulename, "' AS module, im.parent_org AS dr_id, im.org_id AS sr_id,year,quarter,np.network_provider_value,", column_list,
				" FROM ", @table_name, " md ",
				"INNER JOIN import_metadata im ON md.upload_id = im.upload_id ",
				" INNER JOIN station_registrations sr on sr.station_uuid = md.station_uuid ",
				" INNER JOIN network_providers np on sr.network_provider_uuid = np.network_provider_uuid ",
				"WHERE quarter IN (", rpt_quarter, ") AND year IN (", rpt_year, ") AND network_provider_upload IN (", rpt_network_provider, ") AND md.station_uuid IN (",rpt_st_id,") AND im.parent_org IN (",rpt_dr_id,") AND (im.submission_status = 'Submitted' OR im.submission_status = 'Approved')"
			);
			SET @getquarter_to_csv_sr_selected = CONCAT(
				"SELECT '", modulename, "' AS module, im.parent_org AS dr_id, im.org_id AS sr_id, np.network_provider_value,", column_list,
				" FROM ", @table_name, " md ",
				"INNER JOIN import_metadata im ON md.upload_id = im.upload_id ",
				" INNER JOIN station_registrations sr on sr.station_uuid = md.station_uuid ",
				" INNER JOIN network_providers np on sr.network_provider_uuid = np.network_provider_uuid ",
				"WHERE quarter IN (", rpt_quarter, ") AND year IN (", rpt_year, ") AND network_provider_upload IN (", rpt_network_provider, ") AND md.station_uuid IN (",rpt_st_id,") AND im.parent_org IN (",rpt_dr_id,") AND im.org_id IN (",rpt_sr_id,") AND im.submission_status='Approved'"
			);
			SET @getonce_to_csv_dr_or_default = CONCAT(
			"SELECT '", modulename, "' AS module, im.parent_org AS dr_id, im.org_id AS sr_id, np.network_provider_value,", column_list,
			" FROM ", @table_name, " md ",
			"INNER JOIN import_metadata im ON md.upload_id = im.upload_id ",
				" INNER JOIN station_registrations sr on sr.station_uuid = md.station_uuid ",
				" INNER JOIN network_providers np on sr.network_provider_uuid = np.network_provider_uuid ",
			"WHERE md.station_uuid IN (",rpt_st_id,") AND md.network_provider_upload IN (", rpt_network_provider, ") AND im.parent_org IN (",rpt_dr_id,")  AND (im.submission_status = 'Submitted' OR im.submission_status = 'Approved')"
			);

			SET @getonce_to_csv_sr_selected = CONCAT(
				"SELECT '", modulename, "' AS module, im.parent_org AS dr_id, im.org_id AS sr_id, np.network_provider_value,", column_list,
				" FROM ", @table_name, " md ",
				"inner join import_metadata im on md.upload_id = im.upload_id " ,
				" INNER JOIN station_registrations sr on sr.station_uuid = md.station_uuid ",
				" INNER JOIN network_providers np on sr.network_provider_uuid = np.network_provider_uuid "
				"where md.station_uuid in (",rpt_st_id,") and network_provider_upload in (", rpt_network_provider, ") and im.parent_org in (",rpt_dr_id,") and im.org_id in (",rpt_sr_id,") and im.submission_status='Approved'"
			);
			SET @getonce_to_csv_dr_sr = CONCAT(
					"SELECT '", modulename, "' as module, sa.dr_id,sa.sr_id,np.network_provider_value,", column_list,
				" FROM ", @table_name, " md ",
				"inner join import_metadata im on md.upload_id = im.upload_id ",
				"inner join station_authorizations sa on md.station_uuid = sa.station_uuid ",
				" INNER JOIN station_registrations sr on sr.station_uuid = md.station_uuid ",
				" INNER JOIN network_providers np on sr.network_provider_uuid = np.network_provider_uuid "
				"where sa.station_uuid in (",rpt_st_id,") and network_provider_upload in (", rpt_network_provider, ") and sa.dr_id in (",rpt_dr_id,") and sr_id in (",rpt_sr_id,") and im.submission_status='Approved'"
			);
			IF modulename in ('station_registrations') THEN
				IF sr_selected = TRUE THEN
					PREPARE stmt FROM @getstation_to_csv_sr_selected;
				ELSE
					PREPARE stmt FROM @getstation_to_csv_dr_or_default;
				END IF;
			END IF;
			IF modulename in ('module5_data_v3','module7_data_v3') THEN
				IF sr_selected = TRUE THEN
					PREPARE stmt FROM @getannual_to_csv_sr_selected;
				ELSE
					PREPARE stmt FROM @getannual_to_csv_dr_or_default;
				END IF;
			END IF;
			IF modulename in ('module6_data_v3','module8_data_v3','module9_data_v3') THEN
				IF sr_selected = TRUE THEN
					PREPARE stmt FROM @getonce_to_csv_sr_selected;
				ELSE
					PREPARE stmt FROM @getonce_to_csv_dr_or_default;
				END IF;
			END IF;
			IF modulename in ('module2_data_v3','module3_data_v3','module4_data_v3') THEN
				IF sr_selected = TRUE THEN
					PREPARE stmt FROM  @getquarter_to_csv_sr_selected;
				ELSE
					PREPARE stmt FROM@getquarter_to_csv_dr_or_default;
				END IF;
			END IF;
			EXECUTE stmt;
			DEALLOCATE PREPARE stmt;
			IF done THEN
				LEAVE loop_through_csv;
			END IF;
		END LOOP;
	END;
    """
]


def handler(_event, _context):
    conn = aurora.get_connection()
    with conn.cursor() as cursor:
        try:
            for sql in chain(
                    ev_submission_summary,
                    ev_chart_download_modules,
                    ev_chart_populate_port_table,
                    ev_chart_update_station_uuids,
                    ev_chart_download_modules2,
                    ev_chart_update_station_uuids
            ):
                cursor.execute(sql)
        except pymysql.MySQLError as e:
            print("Exception", e)
            print("Exception executing: {ev_submission_summary}")
            raise
        except Exception as e:
            print("Exception", e)
            raise

        conn.commit()
        aurora.close_connection()


if __name__ == "__main__":
    handler(None, None)