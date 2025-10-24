USE evchart_data_v3;

UPDATE module2_data_v3 as mod2 
JOIN station_ports as sp on sp.port_id = mod2.port_id 
SET mod2.port_uuid = sp.port_uuid;

UPDATE module3_data_v3 as mod3
JOIN station_ports as sp on sp.port_id = mod3.port_id 
SET mod3.port_uuid = sp.port_uuid; 

UPDATE module4_data_v3 as mod4 
JOIN station_ports as sp on sp.port_id = mod4.port_id 
SET mod4.port_uuid = sp.port_uuid; 