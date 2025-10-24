"""
InfraDBMigrations

Infrastructure that runs SQL scripts that make changes to the application MySQL database.
"""

import errno
import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict

import pandas as pd
from evchart_helper import aurora
from evchart_helper.custom_exceptions import EvChartFeatureToggleNotFoundError
from evchart_helper.custom_logging import LogEvent
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature
from pymysql.err import OperationalError


def handler(event, context):  # pylint: disable=unused-argument
    try:
        log = LogEvent(event, api="InfraDBMigragions", action_type="READ")
        use_database = "use evchart_data_v3"
        migration_directory = "./migrations"
        # Connect to the MySQL RDS instance
        conn = aurora.get_connection()
        cursor = conn.cursor()

        cursor.execute(use_database)
        migrations = get_migrations(cursor)
        feature_toggle_dict = get_feature_toggle_dict(log)
        feature_toggle_scripts = get_feature_toggled_script_list()
        run_feature_toggle_scripts(
            migration_directory, conn, migrations, feature_toggle_scripts, feature_toggle_dict
        )
    except OperationalError as err:
        print(f"Operational Error: {err}")
        raise
    except Exception as err:
        print(f"Other Error: {err}")
        raise

    finally:
        aurora.close_connection()
        print("Closed cursor and connection")


@dataclass
class FeatureToggledScript:
    file_name: str
    feature_toggle: Feature = None
    backout_file_name: str = None
    requires_backout: bool = False


class ExecutionAction(Enum):
    EXECUTE = "executes original script"
    SKIP = "skips all actions"
    BACKOUT = "runs backout process"


def get_migrations(cursor) -> pd.DataFrame:
    table_exist = check_migration_table_exists(cursor)
    migrations = pd.DataFrame()
    if table_exist:
        try:
            query = "SELECT * FROM migration"
            cursor.execute(query)
            rows = cursor.fetchall()
            column_names = [column[0] for column in cursor.description]
            migrations = pd.DataFrame(rows, columns=column_names)
            print(f"migrations: {migrations}")
        except Exception as e:
            print("Exception at get_migrations", e)
            raise

    return migrations


def check_migration_table_exists(cursor) -> bool:
    try:
        query = "SHOW TABLES LIKE 'migration'"
        cursor.execute(query)
        return cursor.fetchone() is not None
    except Exception as e:
        print("Exception_At_check_migration_table_exists", e)
        raise


def file_already_executed(file_name: str, migrations: pd.DataFrame) -> bool:
    result = False
    if not migrations.empty:
        result = not (migrations[(migrations["script_name"] == file_name)].empty)
    print(f"Migrations_exists: {result}")
    return result


def get_feature_toggle_dict(log) -> Dict[str, bool]:
    feature_toggle_dict = {}
    feature_toggle_service = FeatureToggleService()
    feature_toggle_list = feature_toggle_service.get_all_feature_toggles(log)

    for feature in feature_toggle_list:
        key = feature["Name"]
        value = feature["Value"]
        feature_toggle_dict[key] = value

    return feature_toggle_dict


def get_feature_toggle_value(
    feature_toggled_script: FeatureToggledScript, feature_toggle_dict: Dict[str, bool], log=None
) -> bool:
    toggle_value = False
    if feature_toggled_script.feature_toggle is None:
        toggle_value = True
    else:
        feature_toggle_name = feature_toggled_script.feature_toggle.value
        feature_toggle = feature_toggle_dict.get(feature_toggle_name)

        if feature_toggle is None:
            raise EvChartFeatureToggleNotFoundError(message=f"{feature_toggle_name}", log_obj=log)

        if feature_toggle:
            toggle_value = True

    return toggle_value


def get_feature_toggle_file_list() -> list[FeatureToggledScript]:
    """
    Returns list of FeatureToggledScripts.  Nothing has been done to it yet
    For items with no Feature toggle set feature_toggle to None
    Returns list of FeatureToggledScripts.  Nothing has been done to it yet
    For items with no Feature toggle set feature_toggle to None
    """
    feature_toggled_files = [
        # FeatureToggledScript(
        #     file_name="5014_DB_Migration_Feature_Toggle_Example.sql",
        #     feature_toggle=Feature.DB_MIGRATIONS_FEATURE_TOGGLE_EXAMPLE,
        #     backout_file_name="JE-5015_DB_Migration_Feature_Toggle_Example_backout.sql",
        #     requires_backout=True,
        # ),
        FeatureToggledScript(
            file_name="Module_5_Nullable_Fields.sql", feature_toggle=Feature.MODULE_5_NULLS
        ),
        FeatureToggledScript(
            file_name="je6200_network_provider_table.sql",
        ),
        FeatureToggledScript(
            file_name="JE-6202-populate-network-providers.sql",
        ),
        FeatureToggledScript(
            file_name="JE-6203-network-providers-history.sql",
        ),
        FeatureToggledScript(
            file_name="JE-5925-n-tier-station-authorizations-table-update.sql",
            feature_toggle=Feature.N_TIER_ORGANIZATIONS,
            backout_file_name="JE-5925-n-tier-station-authorizations-table-update-backout.sql",
            requires_backout=True,
        ),
        FeatureToggledScript(
            file_name="JE-6201-populate-np-station-reg.sql",
        ),
        FeatureToggledScript(
            file_name="JE-6325-module-np-uuids.sql"
        ),
        FeatureToggledScript(
            file_name="JE-6209-rename-np-fields.sql"
        ),
        FeatureToggledScript(
            file_name="JE-6209-np-history-update.sql"
        ),
        FeatureToggledScript(
            file_name="JE-5926-n-tier-station-authorizations-table-migrate.sql",
            feature_toggle=Feature.N_TIER_ORGANIZATIONS,
        ),
        FeatureToggledScript(
            file_name="JE-5789-biz-magic-module-5.sql",
            feature_toggle=Feature.ASYNC_BIZ_MAGIC_MODULE_5,
        ),
        FeatureToggledScript(
            file_name="JE-5790-biz-magic-module-9.sql",
            feature_toggle=Feature.ASYNC_BIZ_MAGIC_MODULE_9,
        ),
        FeatureToggledScript(
            file_name="JE-6390-n-tier-import-metadata-columns.sql",
            feature_toggle=Feature.N_TIER_ORGANIZATIONS,
            backout_file_name="JE-6390-n-tier-import-metadata-columns-backout.sql",
            requires_backout=True,
        ),
        FeatureToggledScript(
            file_name="JE-5790-biz-magic-module-9.sql",
            feature_toggle=Feature.ASYNC_BIZ_MAGIC_MODULE_9,
        ),
        FeatureToggledScript(
            file_name="JE-6240-NP-FK.sql"
        ),
        FeatureToggledScript(
            file_name="JE-6437-Add-NPs.sql"
        ),
        FeatureToggledScript(
            file_name="JE-5900-update-kwik-trip.sql"
        ),
        FeatureToggledScript(
        file_name="JE-6540-error-description-expand.sql",
            backout_file_name="JE-6540-error-description-revert.sql",
            feature_toggle=None,
            requires_backout=False,
        ),
        FeatureToggledScript(
            file_name="JE-6230-error-data-create-index.sql",
            backout_file_name="JE-6230-error-data-drop-index.sql",
            feature_toggle=None,
            requires_backout=False,
        ),
        FeatureToggledScript(
            file_name="JE-5302-portid-transfer.sql"
        ),
        FeatureToggledScript(
            file_name="JE-6705_update_tables_with_port_uuid.sql"
        ),
        FeatureToggledScript(
            file_name="JE-6706_set_network_provider_uuid_for_modules.sql"
        ),
        FeatureToggledScript(
            file_name="JE-6803-Update-Station-Registration-Table-Unique-Key.sql",
        ),
        FeatureToggledScript(
            file_name="JE-6804-Module-Data-Upload-UUID-FK.sql",
        ),
        #also adds PK to station_registration
        # FeatureToggledScript(
        #     file_name="JE-6949_FK_station_authorization_to_station_regsistration.sql",
        # ),
        FeatureToggledScript(
            file_name="JE-6989-mod-4-add-excluded_outage-column.sql",
        ),
        FeatureToggledScript(
            file_name="JE-6990-mod-4-add-excluded_outage_reason-column.sql",
        ),
        FeatureToggledScript(
            file_name="JE-6950-fk-ports-ref-registrations.sql",
        ),
        FeatureToggledScript(
            file_name="JE-6991-mod-4-add-excluded_outage_notes-column.sql",
        ),
        FeatureToggledScript(
            file_name="JE-7073-update-power_node_to_electric_era.sql",
        ),
        # commented out until issue is resolved with ports being deleted after data was added
        # FeatureToggledScript(
        #     file_name="JE-6951-fk-mod-data-ports.sql",
        # ),
        FeatureToggledScript(
            file_name="JE-7036-np-updates.sql",
        ),
        FeatureToggledScript(
            file_name="JE-6948-station-uuid-module-data-fk.sql",
        ),
    ]

    return feature_toggled_files


def convert_legacy_files_to_feature_toggled_script(file_list) -> list[FeatureToggledScript]:
    converted_list = []
    if file_list:
        for file_name in file_list:
            converted_file = FeatureToggledScript(file_name=file_name)
            converted_list.append(converted_file)
    return converted_list


def get_legacy_files():
    """
    deprecated way of defining files
    """
    manual_list = [
        "CreateMigrationTable.sql",
        "JE-4038-network-provider-upload.sql",
        "Add_Field_modules_5_6.sql",
        "Create_port_table.sql",
        "Add_Fields_station_registration.sql",
        "Extend_length_of_ports_field.sql",
        "JE-3835-fix-lat-long.sql",
        "JE-4031-new-metadata-status.sql",
        "JE-3666-updates-to-station-registration-table.sql",
        "JE-3696-station-registration-network-provider.sql",
        "JE-4255-Update-Station-Registration.sql",
        "Module_4_Nullable_Fields.sql",
        "JE-4458-sr-submitted-to-approved.sql",
        "JE-4256-bugfix-decision-details.sql",
        "JE-3970-update-m3-m8-datatypes.sql",
        "JE-3658-combine-m9-fields.sql",
        "JE-4039-populate-network-provider-upload.sql",
        "Module_9_Nullable_Fields.sql",
        "JE-4953-update-prod-station-uuids.sql",
        "JE-4592-update-prod-network-providers.sql",
        "je-3994-convert-mod9-null.sql",
        "JE-4981-seed-station-data-2.sql",
        "JE-4981-update-port-fed-funding.sql",
        "je4936_operationaldate_notnull.sql",
        "JE-5034-uptime-nullable.sql",
        "JE-4220-ports-history.sql",
        "Module_2_Nullable_Fields.sql",
        "JE-5300_port_id_updates.sql",
        "JE-5191-m5-projectid-length-change.sql",
        "Nullable_Session_Error.sql",
        "JE-5190-drop-migration-unused-m9.sql",
        "Module_2_Nullable_Fields_Edit.sql",
        "JE-5438-remove-provider-id-mod-2.sql",
        "JE-5519-zero-ack-nullable.sql",
        "JE-5193-station-reg-delete-ports.sql",
        "JE-5460-station-reg-delete-number-of-ports.sql",
        "JE-5780-biz-magic-additions.sql",
        "JE-6087-biz-magic-alteration.sql",
        "JE-5851-update-status-field-with-pending.sql",
        # DO NOT ADD TO THIS LIST USE get_feature_toggle_file_list()
    ]

    return manual_list


def get_feature_toggled_script_list() -> list[FeatureToggledScript]:
    feature_toggled_script_list = []
    legacy_files = get_legacy_files()
    converted_legacy_files = convert_legacy_files_to_feature_toggled_script(legacy_files)
    feature_toggled_script_list.extend(converted_legacy_files)
    feature_toggled_script_list.extend(get_feature_toggle_file_list())
    return feature_toggled_script_list


def check_if_files_in_list_exist(directory, file_name_list):
    sql_files = [f for f in os.listdir(directory) if f.endswith(".sql")]
    for file_name in file_name_list:
        if file_name not in sql_files:
            print("file not found: {file_name}")
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file_name)


def get_execution_action(
    toggle_value, backout_enabled, original_executed, backout_executed
) -> ExecutionAction:
    action = ExecutionAction.SKIP
    if toggle_value:
        if not original_executed:
            action = ExecutionAction.EXECUTE
    else:
        if backout_enabled and original_executed:
            action = ExecutionAction.BACKOUT
        if backout_enabled and backout_executed:
            action = ExecutionAction.SKIP

    return action


def run_feature_toggle_scripts(
    migration_directory,
    connection,
    migrations,
    feature_toggle_scripts: list[FeatureToggledScript],
    feature_toggle_dict,
):

    script_data_collection = collect_script_data(
        migrations, feature_toggle_scripts, feature_toggle_dict
    )
    reversed_collection = reverse_backouts(script_data_collection)

    with connection.cursor() as cursor:
        for script_data in reversed_collection:
            file_name = script_data.get("file_name")
            file_to_remove = script_data.get("file_to_remove")
            if file_to_remove:
                remove_from_migrations_table(cursor, file_to_remove)

            file_path = os.path.join(migration_directory, file_name)
            run_sql_file(cursor, file_path)
            insert_into_migrations_table(cursor, file_name)
            connection.commit()


def collect_script_data(migrations, feature_toggle_scripts, feature_toggle_dict):
    script_data_collection = []
    for toggle_script in feature_toggle_scripts:
        script_data = {}
        original_file_name = toggle_script.file_name
        backout_file = toggle_script.backout_file_name

        original_file_already_executed = file_already_executed(original_file_name, migrations)
        backout_file_already_executed = file_already_executed(backout_file, migrations)

        feature_toggle_is_on = get_feature_toggle_value(toggle_script, feature_toggle_dict)

        execution_action = get_execution_action(
            feature_toggle_is_on,
            toggle_script.requires_backout,
            original_file_already_executed,
            backout_file_already_executed,
        )
        file_name = ""
        file_to_remove = None

        if execution_action == ExecutionAction.SKIP:
            continue
        elif execution_action == ExecutionAction.EXECUTE:
            file_name = original_file_name
            if backout_file_already_executed:
                file_to_remove = backout_file

        elif execution_action == ExecutionAction.BACKOUT:
            file_name = backout_file
            file_to_remove = original_file_name

        script_data = {
            "file_name": file_name,
            "execution_action": execution_action,
            "file_to_remove": file_to_remove,
        }
        script_data_collection.append(script_data)
    return script_data_collection


# get reverse backouts and append executables to end
def reverse_backouts(script_collection):
    backouts = [
        item
        for item in script_collection
        if item.get("execution_action") == ExecutionAction.BACKOUT
    ]
    other_items = [
        item
        for item in script_collection
        if item.get("execution_action") != ExecutionAction.BACKOUT
    ]

    backouts.reverse()
    new_collection = []
    new_collection.extend(backouts)
    new_collection.extend(other_items)

    return new_collection


def run_sql_file(cursor, file_path):
    print(f"executing {file_path}")
    with open(file_path, "r", encoding="utf-8") as file:
        file_text = file.read()
        sql_commands = file_text.split(";")
        for command in sql_commands:
            if command.strip():
                print(f"execute command {command}")
                cursor.execute(command)


def insert_into_migrations_table(cursor, file_name):
    query = "INSERT INTO migration (script_name) VALUES(%s)"
    cursor.execute(query, (file_name))


def remove_from_migrations_table(cursor, file_name):
    query = "DELETE FROM migration WHERE script_name = %s"
    cursor.execute(query, (file_name))


if __name__ == "__main__":
    handler(None, None)
