"""
InfraDBCreateTriggers

Defines and creates the MySQL triggers as part of the application deployment process.
"""
import pymysql
from evchart_helper import aurora


def create_triggers(cursor, database_name):
    tables = {
        "station_registrations": "station_uuid",
        "station_authorizations": "authorization_uuid",
        "import_metadata": "upload_id",
        "station_ports": "port_uuid",
        "network_providers": "network_provider_uuid"
    }

    for table_name, record_id in tables.items():
        cursor.execute(
            "SELECT distinct column_name "
            "FROM information_schema.columns "
            "WHERE table_name = %s AND table_schema = %s "
            "and column_name not in ('updated_on','updated_by')",
            (table_name, database_name)
        )
        columns = cursor.fetchall()
        column_names = [column[0] for column in columns]
        json_columns = ','.join([
            f"'{column}',OLD.{column}" for column in column_names
        ])

        json_columns = json_columns.replace('Data_State', 'NEW')
        update_statements = [
            f"""
            if NOT(old.{c} <=> new.{c}) THEN
                set @changed_data = json_merge_preserve(
                    @changed_data, json_object("{c}", new.{c})
                );
            end if;
            """
            for c in column_names
        ]

        create_insert_trigger = f"""
            CREATE TRIGGER {database_name}.{table_name}_insert_trigger
            AFTER INSERT ON {database_name}.{table_name}
            FOR EACH ROW
            BEGIN
                set @changed_data = JSON_OBJECT(
                    {json_columns.replace('OLD.', 'NEW.')}
                );
                INSERT INTO {database_name}.{table_name}_history (
                    action_type,
                    {record_id},
                    updated_on,
                    updated_by,
                    changed_data
                )
                VALUES (
                    'INSERT',
                    new.{record_id},
                    NOW(),
                    new.updated_by,
                    @changed_data
                );
            END;
        """
        cursor.execute(
            "DROP TRIGGER IF EXISTS "
            f"{database_name}.{table_name}_insert_trigger"
        )
        cursor.execute(create_insert_trigger)

        create_update_trigger = f"""
            CREATE TRIGGER {database_name}.{table_name}_update_trigger
            AFTER UPDATE ON {database_name}.{table_name}
            FOR EACH ROW
            BEGIN
                set @changed_data = JSON_OBJECT();
                {"".join(update_statements)}
                INSERT INTO {database_name}.{table_name}_history (
                    action_type,
                    {record_id},
                    updated_on,
                    updated_by,
                    changed_data
                )
                VALUES (
                    'UPDATE',
                    new.{record_id},
                    NOW(),
                    new.updated_by,
                    @changed_data
                );
            END;
        """

        cursor.execute(
            "DROP TRIGGER IF EXISTS "
            f"{database_name}.{table_name}_update_trigger"
        )
        cursor.execute(create_update_trigger)

        create_delete_trigger = f"""
            CREATE TRIGGER {database_name}.{table_name}_delete_trigger
            BEFORE DELETE ON {database_name}.{table_name}
            FOR EACH ROW
            BEGIN
                set @changed_data = JSON_OBJECT({json_columns});
                INSERT INTO {database_name}.{table_name}_history
                    (action_type, {record_id}, updated_on, changed_data)
                VALUES ('delete', old.{record_id}, NOW(), @changed_data);
            END;
        """
        cursor.execute(
            "DROP TRIGGER IF EXISTS "
            f"{database_name}.{table_name}_delete_trigger"
        )
        cursor.execute(create_delete_trigger)

def handler(_event, _context):
    conn = aurora.get_connection()
    with conn.cursor() as cursor:
        try:
            create_triggers(cursor, "evchart_data_v3")
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
