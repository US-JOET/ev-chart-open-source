USE evchart_data_v3;
ALTER TABLE station_registrations MODIFY column ports VARCHAR(1024);

UPDATE station_registrations
  SET ports = CONCAT_WS(
    ",", 
    "BT112317D0148", "BT112316D0150", "BT112316D0147", "BT112317D0159"
  )
  WHERE station_id = "140109";

UPDATE station_registrations
  SET ports = CONCAT_WS(
    ",", 
    "SI07224741156", "SI07224741158", "SI07224741157", "SI04214340370"
  )
  WHERE station_id = "700083";

UPDATE station_registrations
  SET ports = CONCAT_WS(
    ",", 
    "SI072228440393", "SI072228440394", "SI072228440395", "SI072228440396"
  )
  WHERE station_id = "701127";

UPDATE station_registrations
  SET ports = CONCAT_WS(
    ",", 
    "663d3058ae17be45500add3e", "663d31b31d5ce45d56b58802",
    "663d2f0ac78f84621bbc7929", "663d2d5f2110ef20d5d28dc7"
  )
  WHERE station_id IN (
    "11e7a34f-88ba-4729-803d-06a561",
    "11e7a34f-88ba-4729-803d-06a5616afd69"
  );