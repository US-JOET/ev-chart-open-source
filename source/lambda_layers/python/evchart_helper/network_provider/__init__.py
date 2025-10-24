"""
evchart_helper.network_provider

[Deprecated, moved to DB] Provide a mapping of backend network provider IDs to friendly names.
"""
network_providers_internal = {
    "7charge": "7Charge",
    "abm": "ABM",
    "addenergie": "AddÉnergie",
    "ampedup": "AmpedUp! Networks",
    "ampup": "AmpUp",
    "applegreen_electric": "applegreen electric",
    "autel": "autel",
    "bc_hydro": "BC Hydro",
    "beta_technologies": "Beta Technologies",
    "blink": "Blink",
    "bp_pulse": "bp pulse",
    "chargelab": "ChargeLab",
    "chargenet": "ChargeNet",
    "chargepoint": "ChargePoint",
    "chargesmart_ev": "ChargeSmart EV",
    "chargeup": "ChargeUP",
    "chargie": "Chargie",
    "circlek": "CircleK Charge",
    "circlek_couche_tard_recharge": "CircleK/Couche-Tard Recharge",
    "circuit_electrique": "Circuit électrique",
    "echarge": "eCharge Network",
    "electrify_america": "Electrify America",
    "electrify_canada": "Electrify Canada",
    "enel_x_way": "Enel X Way",
    "envirospark": "EnviroSpark",
    "evbolt": "EVBOLT",
    "ev_connect": "EV Connect",
    "evcs": "EVCS",
    "evgateway": "evGateway",
    "evgo": "EVgo",
    "evmatch": "EVmatch",
    "evpower": "eVPower",
    "ev_range": "EV Range",
    "flash": "FLASH",
    "flo": "FLO",
    "foresta": "Foresta",
    "fpl_evolution": "FPL EVolution",
    "francis_energy": "Francis Energy",
    "graviti_energy": "Graviti Energy",
    "gravity_charging_center": "Gravity Charging Center",
    "honeybadger_charging": "HoneyBadger Charging",
    "hwisel": "Hwisel",
    "incharge": "InCharge",
    "ivy": "Ivy",
    "jule": "Jule",
    "kwik_trip": "Kwik Trip",
    "livingston_energy_group": "Livingston Energy Group",
    "loop": "Loop",
    "matcha_electric": "Matcha Electric",
    "non_networked": "Non-Networked",
    "noodoe": "Noodoe",
    "on_the_run_ev": "On the Run EV",
    "opconnect": "OpConnect",
    "petro_canada": "Petro-Canada",
    "powerflex": "PowerFlex",
    "powernode": "PowerNode",
    "powerport_evc": "PowerPort EVC",
    "powerpump": "PowerPump",
    "red_e_charging": "Red E Charging",
    "revel": "Revel",
    "revitalize_charging_solutions": "Revitalize Charging Solutions",
    "rivian_adventure": "Rivian Adventure Network",
    "rivian_waypoints": "Rivian Waypoints",
    "shell_recharge": "Shell Recharge",
    "stay_n_charge": "Stay-N-Charge",
    "sun_country_highway": "Sun Country Highway",
    "swtch_energy": "SWTCH Energy",
    "tesla_destination": "Tesla Destination",
    "tesla_supercharger": "Tesla Supercharger",
    "turnongreen": "TurnOnGreen",
    "universal_ev_chargers": "Universal EV Chargers",
    "volta": "Volta",
    "wattev": "WattEV",
    "wave": "WAVE",
    "zef": "ZEF Network",
}

network_providers_stylized = {
    stylized: internal for internal, stylized in network_providers_internal.items()
}


def validate_network_provider_name(np):
    if np in network_providers_internal:
        return np
    if np in network_providers_stylized:
        return network_providers_stylized[np]
    return None
