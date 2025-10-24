USE evchart_data_v3;

-- Net new.
INSERT INTO network_providers (network_provider_uuid, network_provider_value, description, is_active)
    VALUES
        (UUID(), "chaevi", "Chaevi", 1),
        (UUID(), "dirtroad", "DirtRoad", 1),
        (UUID(), "epic_charging", "Epic Charging", 1),
        (UUID(), "evoke_systems", "Evoke Systems", 1),
        (UUID(), "evpassport", "EVPassport", 1),
        (UUID(), "ford_charge", "Ford Charge", 1),
        (UUID(), "hyperfuel", "Hyperfuel", 1),
        (UUID(), "ionna", "IONNA", 1),
        (UUID(), "lakeland_ev_charging", "Lakeland EV CHARGING", 1);

-- Rebrand to new.
UPDATE network_providers
    SET
        network_provider_value = "vialynk",
        description = "ViaLynk"
    WHERE network_provider_value = "livingston_energy_group";

-- We don't do FKs in history tables.
ALTER TABLE network_providers_history
    DROP FOREIGN KEY fk_network_providers;

-- Acquired, but no data.
DELETE FROM network_providers
    WHERE network_provider_value = "volta";
