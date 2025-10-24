from unittest.mock import patch
import boto3
from moto import mock_aws
import pytest

from evchart_helper.boto3_manager import Boto3Manager
from evchart_helper.custom_exceptions import EvChartFeatureStoreConnectionError
from evchart_helper.custom_logging import LogEvent
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature

@pytest.fixture
def fixture_ssm_base():
    with mock_aws():
        ssm = boto3.client("ssm")
        ssm.put_parameter(Name="/ev-chart/some_var", Value="true", Type="String")
        yield ssm

@pytest.fixture
def mock_boto3_manager(fixture_ssm_base):
    with patch.object(Boto3Manager, 'client', return_value= fixture_ssm_base) as mock_client:
        yield mock_client

@pytest.fixture
def fixture_ssm_add_2false_and_true(fixture_ssm_base):
    fixture_ssm_base.put_parameter(Name="/ev-chart/features/feature1", Value="False", Type="String")
    fixture_ssm_base.put_parameter(Name="/ev-chart/features/feature2", Value="False", Type="String")
    fixture_ssm_base.put_parameter(Name="/ev-chart/features/add-user", Value="True", Type="String")
    yield fixture_ssm_base

@pytest.fixture
def mock_boto3_manager_extended(fixture_ssm_add_2false_and_true):
    with patch.object(Boto3Manager, 'client', return_value= fixture_ssm_add_2false_and_true) as mock_client:
        yield mock_client

@pytest.fixture
def fixture_ssm_return_12_flags(fixture_ssm_base):
    fixture_ssm_base.put_parameter(Name="/ev-chart/features/feature1", Value="False", Type="String")
    fixture_ssm_base.put_parameter(Name="/ev-chart/features/feature2", Value="False", Type="String")
    fixture_ssm_base.put_parameter(Name="/ev-chart/features/feature3", Value="False", Type="String")
    fixture_ssm_base.put_parameter(Name="/ev-chart/features/feature4", Value="False", Type="String")
    fixture_ssm_base.put_parameter(Name="/ev-chart/features/feature5", Value="False", Type="String")
    fixture_ssm_base.put_parameter(Name="/ev-chart/features/feature6", Value="False", Type="String")
    fixture_ssm_base.put_parameter(Name="/ev-chart/features/feature7", Value="False", Type="String")
    fixture_ssm_base.put_parameter(Name="/ev-chart/features/feature8", Value="False", Type="String")
    fixture_ssm_base.put_parameter(Name="/ev-chart/features/feature9", Value="False", Type="String")
    fixture_ssm_base.put_parameter(Name="/ev-chart/features/feature10", Value="False", Type="String")
    fixture_ssm_base.put_parameter(Name="/ev-chart/features/feature11", Value="False", Type="String")
    fixture_ssm_base.put_parameter(Name="/ev-chart/features/feature12", Value="False", Type="String")
    yield fixture_ssm_base

@pytest.fixture
def mock_boto3_manager_return_12_flags(fixture_ssm_return_12_flags):
    with patch.object(Boto3Manager, 'client', return_value= fixture_ssm_return_12_flags) as mock_client:
        yield mock_client

def test_get_all_feature_toggles_returns_values_in_feature_toggle_path(
    mock_boto3_manager_extended,
):
    log = LogEvent({}, api="", action_type="READ")
    sut = FeatureToggleService()
    feature_flags = sut.get_all_feature_toggles(log)
    assert len(feature_flags) == 3
    assert feature_flags[0]["Name"] == "feature1"
    assert feature_flags[0]["Value"] is False
    assert feature_flags[2]["Name"] == "add-user"
    assert feature_flags[2]["Value"] is True

# pagination fix
def test_get_all_feature_toggles_returns_12_flags(mock_boto3_manager_return_12_flags):
    log = LogEvent({}, api="", action_type="READ")
    sut = FeatureToggleService()
    feature_flags = sut.get_all_feature_toggles(log)
    assert len(feature_flags) == 12


def test_get_all_feature_toggles_returns_empty_when_no_features_exist(mock_boto3_manager):
    sut = FeatureToggleService()
    log = LogEvent({}, api="", action_type="READ")
    feature_flags = sut.get_all_feature_toggles(log)
    assert len(feature_flags) == 0

def test_get_all_feature_toggles_raises_exception_when_unable_to_connect_to_ssm():
    sut = FeatureToggleService()
    log = LogEvent({}, api="", action_type="READ")
    with pytest.raises(EvChartFeatureStoreConnectionError):
        sut.get_all_feature_toggles(log)

def test_get_feature_by_name_value_false(mock_boto3_manager_extended):
    sut = FeatureToggleService()
    log = LogEvent({}, api="", action_type="READ")
    feature_flag = sut.get_feature_toggle_by_name("feature1", log)
    assert feature_flag == "False"

def test_get_feature_by_name_value_true(mock_boto3_manager_extended):
    sut = FeatureToggleService()
    log = LogEvent({}, api="", action_type="READ")
    feature_flag = sut.get_feature_toggle_by_name("add-user", log)
    assert feature_flag == "True"

def test_get_feature_by_name_not_found_returns_empty_object(mock_boto3_manager_extended):
    sut = FeatureToggleService()
    log = LogEvent({}, api="", action_type="READ")
    feature_flag = sut.get_feature_toggle_by_name("Fake", log)
    assert feature_flag is None

def test_get_feature_by_name_given_none_returns_empty_object(mock_boto3_manager_extended):
    sut = FeatureToggleService()
    log = LogEvent({}, api="", action_type="READ")
    feature_flag = sut.get_feature_toggle_by_name(None, log)
    assert feature_flag is None

def test_get_feature_toggle_by_enum_with_valid_enum(mock_boto3_manager_extended):
    sut = FeatureToggleService()
    log = LogEvent({}, api="", action_type="READ")
    feature_flag = sut.get_feature_toggle_by_enum(Feature.ADD_USER, log)
    assert feature_flag == "True"

def test_get_feature_toggle_by_enum_given_str(mock_boto3_manager_extended):
    sut = FeatureToggleService()
    log = LogEvent({}, api="", action_type="READ")
    with pytest.raises(TypeError):
        sut.get_feature_toggle_by_enum(Feature.ADD_USER.value, log)

def test_get_active_feature_toggle_set(mock_boto3_manager_extended):
    sut = FeatureToggleService()
    log = LogEvent({}, api="", action_type="READ")
    res = sut.get_active_feature_toggles(log)
    assert res == {Feature.ADD_USER}

def test_get_active_feature_toggle_set_empty(mock_boto3_manager_return_12_flags):
    sut = FeatureToggleService()
    log = LogEvent({}, api="", action_type="READ")
    res = sut.get_active_feature_toggles(log)
    assert res == {}