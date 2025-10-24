from decimal import Decimal
from unittest.mock import MagicMock, patch
import os

from evchart_helper.custom_exceptions import EvChartDatabaseAuroraQueryError
from APIGetSubmittingNullData.index import check_nulls, biz_magic_check
from feature_toggle.feature_enums import Feature


def cursor():
    return MagicMock()

ft_list = [
    Feature.MODULE_5_NULLS,
    Feature.BIZ_MAGIC,
    Feature.ASYNC_BIZ_MAGIC_MODULE_2,
    Feature.ASYNC_BIZ_MAGIC_MODULE_3,
    Feature.ASYNC_BIZ_MAGIC_MODULE_4,
    Feature.ASYNC_BIZ_MAGIC_MODULE_5,
    Feature.ASYNC_BIZ_MAGIC_MODULE_9
]

mod_2_event = {
    "httpMethod": "GET",
    "requestContext": {
        "accountId": "414275662771",
        "authorizer": {
            "claims": {
                "org_id": "123",
                "org_friendly_id": "1",
                "org_name": "Pennsylania DOT",
                "email": "ebenes@ee.doe.gov",
                "scope": "direct-recipient",
                "preferred_name": "Elaine Benes",
                "role": "admin",
            }
        },
    },
    "headers": {"upload_id": "234324", "module_id": "2"},
}

mod_4_event = {
    "httpMethod": "GET",
    "requestContext": {
        "accountId": "414275662771",
        "authorizer": {
            "claims": {
                "org_id": "123",
                "org_friendly_id": "1",
                "org_name": "Pennsylania DOT",
                "email": "ebenes@ee.doe.gov",
                "scope": "direct-recipient",
                "preferred_name": "Elaine Benes",
                "role": "admin",
            }
        },
    },
    "headers": {"upload_id": "234324", "module_id": "4"},
}

mod_9_event = {
    "httpMethod": "GET",
    "requestContext": {
        "accountId": "414275662771",
        "authorizer": {
            "claims": {
                "org_id": "123",
                "org_friendly_id": "1",
                "org_name": "Pennsylania DOT",
                "email": "ebenes@ee.doe.gov",
                "scope": "direct-recipient",
                "preferred_name": "Elaine Benes",
                "role": "admin",
            }
        },
    },
    "headers": {"upload_id": "234324", "module_id": "9"},
}

mod_5_event = {
  "httpMethod": "GET",
  "requestContext": {
    "accountId": "414275662771",
    "authorizer": {
      "claims": {
        "org_id": "123",
        "org_friendly_id": "1",
        "org_name": "Pennsylania DOT",
        "email": "ebenes@ee.doe.gov",
        "scope": "direct-recipient",
        "preferred_name": "Elaine Benes",
        "role" : "admin"
      }
    }
  },
  "headers": {
      "upload_id": "234324",
      "module_id": "5"
    }
}

from APIGetSubmittingNullData.index import handler as api_get_submitting_null_data


# 200 Submitting null data - mod 4
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetSubmittingNullData.index.FeatureToggleService.get_active_feature_toggles")
@patch("APIGetSubmittingNullData.index.biz_magic_check")
@patch("APIGetSubmittingNullData.index.aurora")
def test_valid_200_mod2(mock_aurora, mock_biz_magic_check, mock_feature_toggle):
    mock_feature_toggle.return_value = {Feature.BIZ_MAGIC, Feature.ASYNC_BIZ_MAGIC_MODULE_2}
    mock_biz_magic_check.return_value = True

    response = api_get_submitting_null_data(mod_2_event, None)
    assert response.get("statusCode") == 200
    assert response.get("body") == True

# 200 Submitting null data - mod 4
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetSubmittingNullData.index.FeatureToggleService.get_active_feature_toggles")
@patch("APIGetSubmittingNullData.index.biz_magic_check")
@patch("APIGetSubmittingNullData.index.aurora")
def test_valid_200_mod4(mock_aurora, mock_biz_magic_check, mock_feature_toggle):
    mock_feature_toggle.return_value = {Feature.BIZ_MAGIC, Feature.ASYNC_BIZ_MAGIC_MODULE_4}
    mock_biz_magic_check.return_value = True

    response = api_get_submitting_null_data(mod_4_event, None)
    assert response.get("statusCode") == 200
    assert response.get("body") == True


# 500 EvChartDatabaseAuroraQueryError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetSubmittingNullData.index.FeatureToggleService.get_active_feature_toggles")
@patch("APIGetSubmittingNullData.index.check_nulls")
@patch("APIGetSubmittingNullData.index.aurora")
def test_invalid_500(mock_aurora, mock_check_nulls, mock_feature_toggle):
    mock_feature_toggle.return_value = ft_list
    mock_check_nulls.side_effect = EvChartDatabaseAuroraQueryError()

    response = api_get_submitting_null_data(mod_4_event, None)
    assert response.get("statusCode") == 500


def test_true_check_nulls():
    mock_cursor = cursor()
    mock_cursor.fetchall.return_value = ((Decimal("123248.92"),), (None,), (None,))

    response = check_nulls("123", 9, cursor=mock_cursor)
    assert response == True


def test_false_check_nulls():
    mock_cursor = cursor()
    mock_cursor.fetchall.return_value = ((Decimal("123248.92"),),)

    response = check_nulls("123", 9, cursor=mock_cursor)
    assert response == False


@patch("APIGetSubmittingNullData.index.execute_query")
def test_true_biz_magic_check(mock_execute):
    mock_cursor = cursor()
    mock_execute.return_value = [{"user_reports_no_data": 1}]
    response = biz_magic_check("123", 9, cursor=mock_cursor)
    assert response == True


@patch("APIGetSubmittingNullData.index.execute_query")
def test_false_biz_magic_check(mock_execute):
    mock_cursor = cursor()
    mock_execute.return_value = [{"user_reports_no_data": 0}]
    response = biz_magic_check("123", 9, cursor=mock_cursor)
    assert response == False


@patch("APIGetSubmittingNullData.index.execute_query")
def test_true_biz_magic_check_no_column(mock_execute):
    mock_cursor = cursor()
    mock_execute.return_value = [{"column": 1}]
    response = biz_magic_check("123", 9, cursor=mock_cursor)
    assert response == False


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetSubmittingNullData.index.FeatureToggleService.get_active_feature_toggles")
@patch("APIGetSubmittingNullData.index.biz_magic_check")
@patch("APIGetSubmittingNullData.index.aurora")
def test_valid_200_bizmagic_mod5(mock_aurora, mock_biz_magic_check, mock_feature_toggle):
    mock_feature_toggle.return_value = {Feature.ASYNC_BIZ_MAGIC_MODULE_5,Feature.BIZ_MAGIC}
    mock_biz_magic_check.return_value = True

    response = api_get_submitting_null_data(mod_5_event, None)
    assert response.get('statusCode') == 200
    assert response.get('body') == True

# 200 Submitting no data - AsyncBizMagic - mod 9
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetSubmittingNullData.index.FeatureToggleService.get_active_feature_toggles")
@patch("APIGetSubmittingNullData.index.biz_magic_check")
@patch("APIGetSubmittingNullData.index.aurora")
def test_valid_200_bizmagic_mod9(
    mock_aurora, mock_biz_magic_check, mock_feature_toggle
):
    mock_feature_toggle.return_value = {Feature.BIZ_MAGIC, Feature.ASYNC_BIZ_MAGIC_MODULE_9}
    mock_biz_magic_check.return_value = True

    response = api_get_submitting_null_data(mod_9_event, None)
    assert response.get("statusCode") == 200
    assert response.get("body") is True
