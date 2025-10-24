-- Change the network provider, powernode to: 
-- Key: electric_era
-- Display name: Electric Era
use evchart_data_v3;

UPDATE network_providers
SET network_provider_value = "electric_era",
`description` = "Electric Era"
WHERE network_provider_value = "powernode";



