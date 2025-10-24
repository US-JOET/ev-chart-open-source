## Configuration File for Database Schema (database_central_config.json)
The database_central_config.json file serves as a centralized configuration for managing the database structure and supports drift detection ensuring consistency across the application.

### File Purpose
- Define names of database tables
- Specify the fields (columns) for each table
- Outline expected module validation and business logic within the field metadata
- List unique key constraints for each table
- List frontend displayed table names and expected grid headers

### File Strucutre
```
{"[database_table_name]": {
        "schema": {
            "[field]": {
                "[field_metadata]": null
            },
        },
    "table_description": "",
    "frequency": "",
    "module_display_name": "",
    "unique_key_constraints": [],
    "left_grid_headers": [],
    "right_grid_headers": []
    }
}
```

- `table_description`: Describe the context of the data in the table
- `frequency`: Submission frequency of module
- `module_display_name`: How the module is displayed within the application
- `unique_key_constraints`: Combinations of fields that need to be unique to prevent duplicates
- `left_grid_headers`: Left column header for the module data page within the application
- `right_grid_headers`: Right column headers for the module data page within the application

### Field Metadata
Every column in the database is listed as a field in the file under the schema of their respective table. Each field has their own metadata that describes its expected properties

- `rds_column_default`: The default database column value
- `rds_is_nullable`: Indicates if the column is a nullable field within the database
- `rds_column_type`: The configured datatype of the column
- `rds_column_key`: Indicates whether a column is part of a key such as a primary key (PRI), unique key (UNI), or indexed(non-unique) column (MUL) to aid in drift detection check. Reference the [MySQL Documentation](https://dev.mysql.com/doc/refman/8.4/en/show-columns.html) under "Key -- Whether the column is indexed" for further explanation regarding the different keys and their purpose
- `reference`: A `KEY: VALUE` pair that identifies the referenced table (`KEY`) and column (`VALUE`) in the case of a column being a foreign key constraint.  `rds_column_key` should be "MUL" for these scenarios.
- `field_description`: The unabbreviated name of the field
- `display_name`: The name displayed within the application
- `module_validation`: The list of valid field descriptions referenced during the module validation process for column based validation
    - `required`: Boolean value flagging if the field is required for every upload, validation will generate an error if field does not exist
    - `is_nullable`: Potentially deprecated field that is predecessor of required_empty_allowed. To be removed when MODULE_[2-9]_NULL feature toggles are removed
    - `required_empty_allowed`: Boolean value describing if field can be left empty due to null acknowledgement rules. If true, then any empty string cells for this field will be ignored, if false, the empty string will be evaluated using the context of the datatype definition
    - `datatype`: Expected datatype
    - `length`: Exact expected input length
    - `min_length`: For string datatypes, to ouline the minimum characters expected
    - `max_length`: For string datatypes, to ouline the maximum characters expected
    - `max_precision`: For decimal datatypes, to outline how many whole number digits are valid
    - `max_scale`: For decimal datatypes, to outline how many decimal digits are valid
    - `min_value`: For decimal and integer datatypes, to outline the minimum value allowed
    - `max_value`: For decimal and integer datatypes, to outline the maximum value allowed
