import os
import json
from typing import Union


class DatabaseCentralConfig:
    """
        Create a class instance to access the database central config.

        The instance can be accessed as a nested object, for example:
            config = DatabaseCentralConfig()

            ev_error_data_schema = config['ev_error_data']['schema']

        Level 1 keys are table names
        Level 2 keys include:
          * schema (dict)
          * table_description (string, in-line documentation)
          * frequency (string literal "one_time", "annual", "quarterly")
          * left_grid_headers (dict of lists)
          * right_grid_headers (dict of lists)

        schema dict keys represent the fields in the table, and the values
        are the RDS details for that field (rds_column_type, etc.)  An
        additional key "module_validation" includes information used to
        validate uploads of that module by default or if a feature toggle
        is enabled, if required
    """
    def __init__(
        self,
        path: str = os.path.join(
            "/",
            "opt",
            "python",
            "database_central_config",
            "database_central_config.json"
        )
    ):
        with open(file=path, mode="r", encoding="utf-8") as config_json:
            self._config = json.load(config_json)

    def __repr__(self):
        return json.dumps(self._config)

    def get(self, key: str):
        return self._config.get(key)

    def __getitem__(self, key: str):
        return self._config[key]

    def __contains__(self, key: str):
        return key in self._config

    def __iter__(self):
        return iter(self._config.items())

    def keys(self):
        return iter(self._config.keys())

    def module_config(self, module_id: Union[int | str]) -> dict:
        """
            Return configuration information regardless if the module is
            called by full table name, or integer or string single digit.
            For example, each of the below commands will return equivalent
            results:

                config.module_config("module2_data_v3")

                config.module_config("2")

                config.module_config(2)
        """
        module_ids_int = set(range(2, 10))
        module_ids_str = {str(m) for m in module_ids_int}

        if (
            (isinstance(module_id, int) and module_id in module_ids_int) or
            (isinstance(module_id, str) and module_id in module_ids_str)
        ):
            return self._config[f"module{module_id}_data_v3"]
        return self._config[module_id]

    def skip_validation(self, table_name: Union[int | str]) -> list:
        """
            Convenience function to determine which fields for a particular
            module do not require structural validation
        """
        return [
            key
            for key, value in self.module_config(table_name)['schema'].items()
            if value.get('module_validation', {}) == {}
        ]

    def all_fields_for_module(self, table_name: Union[int | str], feature_toggle_set: set = frozenset()) -> dict:
        """
            A function to return all fields for a particular module.
        """
        if isinstance(table_name, int):
            table_name = f"module{table_name}_data_v3"

        module_fields = {
            key: value.get('module_validation', {}).get('default', {})
            for key, value in self.module_config(table_name)['schema'].items()
        }

        return module_fields

    def module_validation(self, table_name: Union[int | str], feature_toggle_set: set = frozenset()) -> dict:
        """
            Convenience function to determine which fields for a particular
            module are required but allowed to be empty
        """
        if isinstance(table_name, int):
            table_name = f"module{table_name}_data_v3"

        initial_module_validations = {
            key: value.get('module_validation', {}).get('default', {})
            for key, value in self.module_config(table_name)['schema'].items()
        }
        module_validations = {key: value for key, value in initial_module_validations.items() if value != {}}
        return module_validations

    def required_fields(
        self,
        table_name: Union[int | str],
        feature_toggle_set: set = frozenset()
    ) -> dict:
        """
            Convenience function to return the required fields for a particular module
        """
        module_validations = self.all_fields_for_module(table_name)
        for field, validation in module_validations.items():
            for ft in feature_toggle_set:
                validation.update(
                    self.module_config(table_name)['schema'][field]
                    .get('module_validation', {}).get(ft.value, {})
                )

        return {
            key for key, value in module_validations.items()
            if value.get('required', False)
        }

    def recommended_fields(
        self,
        table_name: Union[int | str],
        feature_toggle_set: set = frozenset()
    ) -> dict:
        """
            Convenience function to return the recommended fields for a particular module
        """
        module_validations = self.all_fields_for_module(table_name)
        for field, validation in module_validations.items():
            for ft in feature_toggle_set:
                validation.update(
                    self.module_config(table_name)['schema'][field]
                    .get('module_validation', {}).get(ft.value, {})
                )

        return {
            key for key, value in module_validations.items()
            if not value.get('required', False) and value.get('required_empty_allowed', False)
        }

    def required_empty_allowed_fields(
        self,
        table_name: Union[int | str],
        feature_toggle_set: set = frozenset()
    ) -> dict:
        """
            Convenience function to determine which fields for a particular
            module are required but allowed to be empty
        """
        if isinstance(table_name, int):
            table_name = f"module{table_name}_data_v3"

        module_validations = {
            key: value.get('module_validation', {}).get('default', {})
            for key, value in self.module_config(table_name)['schema'].items()
        }
        for field, validation in module_validations.items():
            for ft in feature_toggle_set:
                validation.update(
                    self.module_config(table_name)['schema'][field]
                    .get('module_validation', {}).get(ft.value, {})
                )

        return {
            key for key, value in module_validations.items()
            if (
                value.get('required', False) and
                value.get('required_empty_allowed', False)
            )
        }

    def module_frequency(self, module_id: Union[int | str]) -> str:
        """
            Returns "one_time", "annual", "quarterly" based on module_id
        """
        return self.module_config(module_id).get('frequency')

    def module_frequency_proper(self, module_id: Union[int | str]) -> str:
        """
            Returns "One-Time", "Annual", "Quarterly" based on module_id
        """
        return {
            'annual': 'Annual',
            'quarterly': 'Quarterly',
            'one_time': 'One-Time'
        }.get(self.module_frequency(module_id))

    def module_frequency_quarter(self, quarter: Union[int | str]) -> str:
        """
            Returns "Quarter 1 (Jan-Mar)", "Quarter 2 (Apr-Jun)",
            "Quarter 3 (Jul-Sep)", or "Quarter 4 (Oct-Dec)" based on quarter
        """
        return {
            "1": "Quarter 1 (Jan-Mar)",
            "2": "Quarter 2 (Apr-Jun)",
            "3": "Quarter 3 (Jul-Sep)",
            "4": "Quarter 4 (Oct-Dec)",
        }.get(str(quarter), "INVALID QUARTER")

    def module_grid_display_headers(self, module_id: Union[int | str]) -> dict:
        """
            Returns object with the left-side (fixed) and
            right-side (scrolling) headers used when rendering module data
            in the UI, based on module_id or table name
        """
        return {
            "left_grid_headers":
                self.module_config(module_id).get('left_grid_headers'),
            "right_grid_headers":
                self.module_config(module_id).get('right_grid_headers')
        }

    def rds_boolean_fields(
        self, table_name: Union[int | str | None] = None
    ) -> set:
        """
            Returns set of column names defined in the schema as
            tinyint(1), that should be rendered as boolean in UI,
            based on module_id or table name.  If no argument is provided,
            return all defined tinyint(1) fields.

            To get boolean fields as defined in data validation rules,
            use validated_boolean_fields()
        """
        if not table_name:
            # merge the return values (set) from all defined tables
            # into one set, and return
            return set.union(*[
                self.rds_boolean_fields(table) for table in self._config.keys()
            ])
        return {
            key
            for key, value in self.module_config(table_name)['schema'].items()
            if value.get("rds_column_type") == "tinyint(1)"
        }

    def unique_key_constraints(
        self, module_id: Union[int | str]
    ) -> list:
        """
            Returns list of the unique key constrained fields,
            based on module_id
        """
        return self.module_config(module_id)["unique_key_constraints"]

    def module_field_display_names(self, module_id: Union[int | str]) -> dict:
        """
            Returns object of column name/description pairs,
            based on module_id or table name
        """

        return {
            key: self.module_config(module_id)['schema'][key]['display_name']
            for key in (
                self.module_config(module_id).get('left_grid_headers') +
                self.module_config(module_id).get('right_grid_headers')
            )
        }

    def table_description(self, module_id: Union[int | str]) -> str:
        """
            Returns table description based on module_id
        """
        return self.module_config(module_id).get('table_description')

    def quarterly_module_ids(self) -> list:
        """
            Returns list of module numbers (as string) that have
            quarterly submission frequency
        """
        return [
            str(m)
            for m in range(2, 10)
            if self.module_config(m).get('frequency') == "quarterly"
        ]

    def onetime_module_ids(self) -> list:
        """
            Returns list of module numbers (as string) that have
            one-time ubmission frequency
        """
        return [
            str(m)
            for m in range(2, 10)
            if self.module_config(m).get('frequency') == "one_time"
        ]

    def annual_module_ids(self) -> list:
        """
            Returns list of module numbers (as string) that have
            annual submission frequency
        """
        return [
            str(m)
            for m in range(2, 10)
            if self.module_config(m).get('frequency') == "annual"
        ]

    def module_display_name(self, module_id: Union[int | str]) -> str:
        """
            Returns module display name based on module_id
        """
        return self.module_config(module_id).get('module_display_name')

    def validated_boolean_fields(self, table_name: Union[int | str]) -> set:
        """
            Returns set of column names defined in the validation rules as
            boolean

            To get boolean fields as defined in database schema,
            use rds_boolean_fields()
        """
        return {
            key
            for key, value in self.module_config(table_name)['schema'].items()
            if value.get("module_validation", {}).get('default', {}).get("datatype") == "boolean"
        }

    def validated_datetime_fields(self, table_name: Union[int | str]) -> set:
        """
            Returns set of column names defined in the validation rules as
            datetime

        """
        return {
            key
            for key, value in self.module_config(table_name)['schema'].items()
            if value.get("module_validation", {}).get('default', {}).get("datatype") == "datetime"
        }

    def validated_numeric_fields(self, table_name: Union[int | str]) -> set:
        """
            Returns set of column names defined in the validation rules as
            decimal or integer

        """
        return {
            key
            for key, value in self.module_config(table_name)['schema'].items()
            if value.get("module_validation", {}).get('default', {}).get("datatype") in {
                "decimal", "integer"
            }
        }
