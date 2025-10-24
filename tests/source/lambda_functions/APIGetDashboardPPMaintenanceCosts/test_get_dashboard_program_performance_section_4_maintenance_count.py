import datetime
from decimal import Decimal

from APIGetDashboardPPMaintenanceCosts.index import (  # type: ignore
    count_section4_maintenance_cost
)


def test_count_section4_maintenance_cost():
    maintenance_costs_sample = [
        {
            "station_uuid": "a1",
            "year": 2024,
            "operational_date": datetime.date(year=2024, month=1, day=1),
            "maintenance_cost_total": Decimal(360.0),
            # normalized monthly cost is 30.0
        },
        {
            "station_uuid": "b2",
            "year": 2024,
            "operational_date": datetime.date(year=2024, month=1, day=1),
            "maintenance_cost_total": Decimal(720.0),
            # normalized monthly cost is 60.0
        },
        {
            "station_uuid": "c3",
            "year": 2024,
            "operational_date": datetime.date(year=2026, month=5, day=14),
            "maintenance_cost_total": Decimal(24.0),
            # record will be skipped because operational_date is
            # later than reporting year
        },
    ]

    response = count_section4_maintenance_cost(maintenance_costs_sample)
    # average of 30.0 and 60.0 is 45.0
    assert response.get("monthly_avg_maintenance_repair_cost") == 45.0
    assert response.get("maintenance_cost_metrics_available")


def test_count_section4_maintenance_cost_zero_division_error():
    response = count_section4_maintenance_cost([])
    assert response.get("monthly_avg_maintenance_repair_cost") is None
    assert not response.get("maintenance_cost_metrics_available")

