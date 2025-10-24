-- Change the network provider, kwik_trip to: 
-- Key: KWIK_CHARGE
-- Display name: Kwik Charge by Kwik Trip
use evchart_data_v3;

UPDATE network_providers
SET description = 'Kwik Charge by Kwik Trip'
WHERE network_provider_value = 'kwik_trip';

UPDATE network_providers
SET network_provider_value = 'kwik_charge'
WHERE description = 'Kwik Charge by Kwik Trip';

