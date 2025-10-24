import os
import sys
from unittest.mock import MagicMock, patch
import pytest
import copy

sys.path.extend(
    [".", "source/lambda_layers/python", "source/lambda_functions"]
)

from database_central_config import DatabaseCentralConfig
from feature_toggle.feature_enums import Feature

fed_funded_station_data = {
    'address': '123 nice lane',
    'city': 'san diego ',
    'project_type': 'new_station',
    'station_id': 'station1',
    'latitude': '12.123456',
    'longitude': '12.123456',
    'nickname': 'station1',
    'federally_funded': True,
    'num_fed_funded_ports': '1',
    'num_non_fed_funded_ports': None,
    'state': 'ca',
    'status': 'Active',
    'network_provider': 'abm',
    'operational_date': '2025-07-04',
    'NEVI': 1,
    'CFI': 1,
    'EVC_RAA': 0,
    'CMAQ': 0,
    'CRP': 0,
    'OTHER': 0,
    'AFC': 1,
    'authorized_subrecipients': [],
    'zip': '12345',
    'zip_extended': '1234',
    'fed_funded_ports': [{'port_id': '123', 'port_type': 'DCFC'}],
    'non_fed_funded_ports': [],
    'dr_id': '11111111-2222-3333-4444-555555555555'
}

non_fed_funded_station_data = {
    'address': '123 not nice lane',
    'city': 'San Diego',
    'project_type': 'new_station',
    'station_id': 'station-unfunded',
    'latitude': '12.123456',
    'longitude': '12.123456',
    'nickname': 'station-unfunded',
    'federally_funded': False,
    'num_fed_funded_ports': 0,
    'num_non_fed_funded_ports': '2',
    'state': 'ca',
    'status': 'Active',
    'network_provider': 'chargepoint',
    'operational_date': '2025-07-07',
    'NEVI': 0,
    'CFI': 0,
    'EVC_RAA': 0,
    'CMAQ': 0,
    'CRP': 0,
    'OTHER': 0,
    'AFC': 0,
    'authorized_subrecipients': [],
    'zip': '12345',
    'zip_extended': '1234',
    'fed_funded_ports': [],
    'non_fed_funded_ports': [
        {'port_id': '1234', 'port_type': ''},
        {'port_id': '65489', 'port_type': 'L2'}
    ],
    'dr_id': '11111111-2222-3333-4444-555555555555'
}

auth_token = {
    "org_id": '11111111-2222-3333-4444-555555555555',
    "org_friendly_id": "1",
    "org_name": "New York DOT",
    "email": "gcostanza@gmail.com",
    "preferred_name": "George Costanza",
    "recipient_type": "direct-recipient",
    "role": "admin",
    "name": "John Bardeen"
}

@pytest.fixture(name="validation_options_for_federally_funded_station")
def get_validation_options_for_fed_funded_station():
    validation_options = {
        "api": "post",
        "station": fed_funded_station_data,
        "auth_values": auth_token,
        "feature_toggle_set": {
            Feature.NETWORK_PROVIDER_TABLE,
            Feature.SR_ADDS_STATION,
            Feature.REGISTER_NON_FED_FUNDED_STATION,
            Feature.DATABASE_CENTRAL_CONFIG
        },
        "cursor": MagicMock()
    }
    return copy.deepcopy(validation_options)


@pytest.fixture(name="validation_options_for_non_federally_funded_station")
def get_validation_options_for_non_fed_funded_station():
    validation_options = {
        "api": "post",
        "station": non_fed_funded_station_data,
        "auth_values": auth_token,
        "feature_toggle_set": {
            Feature.NETWORK_PROVIDER_TABLE,
            Feature.SR_ADDS_STATION,
            Feature.REGISTER_NON_FED_FUNDED_STATION,
            Feature.DATABASE_CENTRAL_CONFIG
        },
        "cursor": MagicMock()
    }
    return copy.deepcopy(validation_options)

@pytest.fixture(scope="module")
def mock_config():
    config = DatabaseCentralConfig(
        path=os.path.join(
            ".",
            "source",
            "lambda_layers",
            "python",
            "database_central_config",
            "database_central_config.json"
        )
    )

    # using patch to mock the call to DatabaseCentralConfig
    with patch(f"station_validation.validate_data_integrity.DatabaseCentralConfig", return_value=config) as mock:
        yield mock
