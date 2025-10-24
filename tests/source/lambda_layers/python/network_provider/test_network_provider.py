from evchart_helper.network_provider import (
    validate_network_provider_name,
    network_providers_internal,
    network_providers_stylized
)


def test_np_internal():
    assert network_providers_internal["ev_connect"] == "EV Connect"


def test_np_stylized():
    assert network_providers_stylized["EV Connect"] == "ev_connect"


def test_np_validation():
    assert validate_network_provider_name("ev_connect") == "ev_connect"
    assert validate_network_provider_name("EV Connect") == "ev_connect"
    assert validate_network_provider_name("does not exist") is None
