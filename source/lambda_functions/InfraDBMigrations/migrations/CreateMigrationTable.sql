use evchart_data_v3;
CREATE TABLE migration (
   script_name VARCHAR(100) NOT NULL,
   executed_on DATETIME DEFAULT CURRENT_TIMESTAMP,
   PRIMARY KEY (script_name)
);

