import csv
import pytest

from module_validation import (
    module_definitions
)


@pytest.fixture(name="json_module_and_field_pairs")
def fixture_json_module_and_field_pairs():
    return [
        (f"module{id}_data_v3", field_name)
        for id in range(2, 10)
        for field_name in module_definitions.get(id).get('required_data') +
        module_definitions.get(id).get('recommended_data')
    ]


@pytest.fixture(name="db_module_and_field_pairs")
def fixture_db_module_and_field_pairs():
    with open(
        "./source/lambda_functions/InfraInitDBTables/ev_table.csv",
        "r", encoding="utf-8"
    ) as fh:
        reader = csv.reader(fh)
        return {
            (row[2], row[3]) for row in reader
            if row[2].startswith('module')
            and row[3] not in {"upload_id", "station_id"}
        }


@pytest.mark.skip("deprecating ev_table.csv as schema reference")
def test_json_module_elements_defined_in_db(
    json_module_and_field_pairs, db_module_and_field_pairs
):
    for json_pair in json_module_and_field_pairs:
        assert json_pair in db_module_and_field_pairs
