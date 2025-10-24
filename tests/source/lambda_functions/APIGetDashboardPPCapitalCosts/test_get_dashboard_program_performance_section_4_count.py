from unittest.mock import patch, MagicMock
from decimal import Decimal

from APIGetDashboardPPCapitalCosts.index import (  # type: ignore
    count_section4_capital_cost,
    capital_costs
)

def test_count_section4_capital_cost():
    capital_costs_sample = [
        {
            "nevi": 1,
            "station_uuid": "nevi1",
            "der_cost_total": Decimal(12.0),
            "der_cost_federal": Decimal(9.0),
            "der_install_cost_total": Decimal(12.0),
            "der_install_cost_federal": Decimal(9.0),
            "distribution_cost_total": Decimal(12.0),
            "distribution_cost_federal": Decimal(9.0),
            "equipment_cost_total": Decimal(12.0),
            "equipment_cost_federal": Decimal(9.0),
            "equipment_install_cost_total": Decimal(12.0),
            "equipment_install_cost_federal": Decimal(9.0),
            "real_property_cost_total": Decimal(12.0),
            "real_property_cost_federal": Decimal(9.0),
            "service_cost_total": Decimal(12.0),
            "service_cost_federal": Decimal(9.0),
            "dist_sys_cost_total": Decimal(12.0),
            "dist_sys_cost_federal": Decimal(9.0),
        },
        {
            "nevi": 0,
            "station_uuid": "antinevi",
            "der_cost_total": None,
            "der_cost_federal": None,
            "der_install_cost_total": None,
            "der_install_cost_federal": None,
            "distribution_cost_total": None,
            "distribution_cost_federal": None,
            "equipment_cost_total": None,
            "equipment_cost_federal": None,
            "equipment_install_cost_total": None,
            "equipment_install_cost_federal": None,
            "real_property_cost_total": None,
            "real_property_cost_federal": None,
            "service_cost_total": None,
            "service_cost_federal": None,
            "dist_sys_cost_total": None,
            "dist_sys_cost_federal": None,
        },
    ]

    response = count_section4_capital_cost(capital_costs_sample)
    assert response["federal_funding"] == 36.0
    assert response["nonfederal_funding"] == 12.0
    assert response["capital_costs_total_nevi"] == 48.0
    assert response["average_nevi_capital_cost"] == 48.0
    assert response["capital_cost_metrics_available"]


def test_count_section4_capital_cost_zero_division_error():
    response = count_section4_capital_cost([])
    assert response["federal_funding"] == 0.0
    assert response["nonfederal_funding"] == 0.0
    assert response["capital_costs_total_nevi"] == 0.0
    assert response["average_nevi_capital_cost"] is None
    assert not response["capital_cost_metrics_available"]

@patch("APIGetDashboardPPCapitalCosts.index.execute_query_with_filters")
def test_capital_costs(mock_execute_query_with_filters):
    capital_costs_one_row = tuple(["abc123"] + [float(x) for x in range(17)])
    mock_execute_query_with_filters.return_value = (capital_costs_one_row,)

    response = capital_costs(MagicMock(), "dr123")
    assert len(response) == 1
    assert response[0].get("dist_sys_cost_federal") == 8.0
