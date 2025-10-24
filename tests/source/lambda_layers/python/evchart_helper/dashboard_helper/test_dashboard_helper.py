import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest

from evchart_helper.custom_exceptions import EvChartMissingOrMalformedHeadersError
from evchart_helper.dashboard_helper import (
    execute_query_with_filters,
    get_dr_id,
    get_prior_quarter_window,
    get_station,
    get_sr_id,
    operational_days,
    validate_org,
    generate_query_filters,
    normalized_monthly_cost
)
import feature_toggle


@pytest.fixture(name="event")
def get_valid_event():
    return {
        "headers": {},
        "httpMethod": "GET",
        "requestContext": {
            "accountId": "414275662771",
            "authorizer": {
                "claims": {
                    "org_id": "123",
                    "org_friendly_id": "1",
                    "org_name": "JOET",
                    "email": "dev@ee.doe.gov",
                    "scope": "joet",
                    "role": "admin",
                }
            },
        },
        "queryStringParameters": {
            "dr_id": "All",
        },
    }


@patch.object(target=feature_toggle.FeatureToggleService, attribute="get_feature_toggle_by_enum")
def test_validate_org_jo(mock_auth):
    mock_auth = {
        "org_id": "1234",
        "recipient_type": "joet",
        "name": "JOET",
        "org_friendly_id": "99",
    }
    statement = validate_org(mock_auth)
    assert statement == "JO"


@patch.object(target=feature_toggle.FeatureToggleService, attribute="get_feature_toggle_by_enum")
def test_validate_org_dr(mock_auth):
    mock_auth = {
        "org_id": "1234",
        "recipient_type": "direct-recipient",
        "name": "DR",
        "org_friendly_id": "99",
    }
    statement = validate_org(mock_auth)
    assert statement == "DR"


@pytest.mark.parametrize("default_dr_id", ["All"])
def test_get_dr_id(default_dr_id, event):
    event["queryStringParameters"] = {
        "dr_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
    }
    path_parameters = event["queryStringParameters"]
    dr_id = get_dr_id(path_parameters, default_dr_id)

    expected_dr_id = "3824c24b-f4fa-44bb-b030-09e99c3e4b6c"
    assert expected_dr_id == dr_id


# test get_dr_id where no query parameters are provided
@pytest.mark.parametrize("path_parameters", [{}])
@pytest.mark.parametrize("default_dr_id", ["All"])
def test_get_dr_id_with_no_path_parameters(default_dr_id, path_parameters):
    dr_id = get_dr_id(path_parameters, default_dr_id)

    expected_dr_id = default_dr_id
    assert expected_dr_id == dr_id


@pytest.mark.parametrize("default_sr_id", ["All"])
def test_get_sr_id(default_sr_id, event):
    event["queryStringParameters"] = {
        "sr_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
    }
    path_parameters = event["queryStringParameters"]
    sr_id = get_sr_id(path_parameters, default_sr_id)

    expected_sr_id = "3824c24b-f4fa-44bb-b030-09e99c3e4b6c"
    assert expected_sr_id == sr_id


@pytest.mark.parametrize("default_sr_id", ["All"])
def test_get_sr_id_no_parameters(default_sr_id):
    sr_id = get_sr_id(None, default_sr_id)

    assert default_sr_id == sr_id


@pytest.mark.parametrize("default_station", ["123"])
def test_get_station(default_station, event):
    event["queryStringParameters"] = {
        "year": "2023",
    }
    path_parameters = event["queryStringParameters"]
    station = get_station(path_parameters=path_parameters, default_station=default_station)

    expected_station = "123"
    assert expected_station == station


@pytest.mark.parametrize("path_parameters", [{}])
@pytest.mark.parametrize("default_station", ["123"])
def test_get_station_with_no_path_parameters(default_station, path_parameters):
    station = get_station(path_parameters, default_station)

    expected_station = default_station
    assert expected_station == station


def test_default_dr_id():
    assert get_dr_id(None, "ALL") == "ALL"


@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
def test_generate_filters_ft_on(mock_get_feature_by_enum):
    mock_get_feature_by_enum.return_value = "True"
    filters = {"dr_id": "All", "year": "2024", "sr_id": "All"}
    logger = MagicMock()
    response = generate_query_filters(filters, logger)
    assert "status = 'Active'" in response


def test_generate_filters_ft_off():
    filters = {"dr_id": "All", "year": "2024", "sr_id": "All"}
    logger = MagicMock()
    response = generate_query_filters(filters, logger)
    assert "status = 'Active'" not in response


def test_group_by_clause():
    mock_cursor = MagicMock()
    logger = MagicMock()

    execute_query_with_filters(
        cursor=mock_cursor,
        query="NOT A QUERY ",
        filters={"dr_id": "All", "sr_id": "All", "year": "2024", "station": "All"},
        group_by=["dr_id"],
        logger=logger,
    )
    execute_args, _ = mock_cursor.execute.call_args
    assert len(execute_args) == 2
    assert execute_args[0] == (
        "NOT A QUERY "
        " AND dr_id <> '154ecdd3-d864-4110-916b-9c1287bb31e8' "
        " AND year = %(year)s "
        " GROUP BY dr_id "
    )


def test_group_by_clause_year():
    mock_cursor = MagicMock()
    logger = MagicMock()

    execute_query_with_filters(
        cursor=mock_cursor,
        query="NOT A QUERY ",
        filters={"dr_id": "All", "sr_id": "All", "year": "NA", "station": "All"},
        group_by=["dr_id"],
        logger=logger,
    )
    execute_args, _ = mock_cursor.execute.call_args
    assert len(execute_args) == 2
    assert execute_args[0] == (
        "NOT A QUERY "
        " AND dr_id <> '154ecdd3-d864-4110-916b-9c1287bb31e8' "
        " AND year = %(year)s "
        " GROUP BY dr_id "
    )


def test_group_by_clause_station():
    mock_cursor = MagicMock()
    logger = MagicMock()

    execute_query_with_filters(
        cursor=mock_cursor,
        query="NOT A QUERY ",
        filters={"dr_id": "dr456", "sr_id": "sr789", "year": "NA", "station": "123"},
        group_by=["dr_id"],
        logger=logger,
    )
    execute_args, _ = mock_cursor.execute.call_args
    assert len(execute_args) == 2
    assert execute_args[0] == (
        "NOT A QUERY "
        " AND dr_id = %(dr_id)s "
        " AND evchart_data_v3.station_registrations.station_uuid IN ( "
        "   SELECT station_uuid from evchart_data_v3.station_authorizations "
        "    WHERE dr_id = %(dr_id)s and sr_id = %(sr_id)s "
        ")  "
        "AND evchart_data_v3.station_registrations.station_uuid = %(station)s "
        " AND year = %(year)s "
        " GROUP BY dr_id "
    )


def test_group_by_clause_invalid_type():
    mock_cursor = MagicMock()
    logger = MagicMock()

    with pytest.raises(EvChartMissingOrMalformedHeadersError):
        execute_query_with_filters(
            cursor=mock_cursor,
            query="NOT A QUERY ",
            filters={"dr_id": "All", "sr_id": "All", "year": "2024", "station": "All"},
            group_by="dr_id",
            logger=logger,
        )


def test_operational_days():
    # year in import_metadata is a varchar(4)
    assert operational_days(datetime.date(year=2023, month=12, day=1), reporting_year="2023") == 31
    assert (
        operational_days(
            operational_date=datetime.date(year=2023, month=1, day=2), reporting_year="2023"
        )
        == 364
    )
    assert (
        operational_days(
            operational_date=datetime.date(year=2023, month=1, day=1), reporting_year="2023"
        )
        == 365
    )
    assert (
        operational_days(
            operational_date=datetime.date(year=2023, month=12, day=31), reporting_year="2024"
        )
        == 365
    )
    assert (
        operational_days(
            operational_date=datetime.date(year=2025, month=4, day=18), reporting_year="2024"
        )
        == 0
    )

    # disregard leap years for now
    assert (
        operational_days(
            operational_date=datetime.date(year=2024, month=1, day=2), reporting_year="2024"
        )
        == 365
    )
    assert (
        operational_days(
            operational_date=datetime.date(year=2024, month=1, day=1), reporting_year="2024"
        )
        == 365
    )


def test_normalized_monthly_cost():
    assert normalized_monthly_cost(Decimal(360.0), 365) == pytest.approx(30.0)
    assert normalized_monthly_cost(Decimal(360.0), 182.5) == pytest.approx(60.0)
    assert normalized_monthly_cost(Decimal(360.0), 30) == pytest.approx(365.0)
    assert normalized_monthly_cost(Decimal(12.0), 1) == pytest.approx(365.0)


@pytest.mark.parametrize(
    "today,start,end",
    [
        (
            datetime.date(year=2023, month=12, day=31),
            datetime.date(year=2022, month=10, day=1),
            datetime.date(year=2023, month=9, day=30),
        ),
        (
            datetime.date(year=2024, month=1, day=1),
            datetime.date(year=2023, month=1, day=1),
            datetime.date(year=2023, month=12, day=31),
        ),
        (
            datetime.date(year=2024, month=3, day=31),
            datetime.date(year=2023, month=1, day=1),
            datetime.date(year=2023, month=12, day=31),
        ),
        (
            datetime.date(year=2024, month=4, day=1),
            datetime.date(year=2023, month=4, day=1),
            datetime.date(year=2024, month=3, day=31),
        ),
        (
            datetime.date(year=2024, month=6, day=30),
            datetime.date(year=2023, month=4, day=1),
            datetime.date(year=2024, month=3, day=31),
        ),
        (
            datetime.date(year=2024, month=7, day=1),
            datetime.date(year=2023, month=7, day=1),
            datetime.date(year=2024, month=6, day=30),
        ),
        (
            datetime.date(year=2024, month=9, day=30),
            datetime.date(year=2023, month=7, day=1),
            datetime.date(year=2024, month=6, day=30),
        ),
        (
            datetime.date(year=2024, month=10, day=1),
            datetime.date(year=2023, month=10, day=1),
            datetime.date(year=2024, month=9, day=30),
        ),
    ],
)
def test_prior_quarter(today, start, end):
    assert get_prior_quarter_window(today)["start"] == start
    assert get_prior_quarter_window(today)["end"] == end


def test_prior_quarter_cache():
    get_prior_quarter_window(datetime.date(2025, 2, 3))
    cache_hits = get_prior_quarter_window.cache_info().hits

    get_prior_quarter_window(datetime.date(2025, 2, 3))
    assert get_prior_quarter_window.cache_info().hits == cache_hits + 1
