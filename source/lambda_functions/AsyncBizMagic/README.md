## AsyncBizMagic

### Background
- AsyncBizMagic acts as a 3rd step in the current 4 step data validation process for uploading module data
- Row-based validation is performed across each module upload to ensure that the data meets business requirements for its respective module before being accepted into the EV-Chart Application
- Modules 2, 3, 4, 5 & 9 are allowed to be submitted with empty values for specific data fields when no relevant data can be given for a reporting period
    - This allows the system to comprehensively track data reporting, disambiguating whether there were no relevant data for a given station or port in a reporting period or if no data has been yet uploaded for that station or port and reporting period
    - Conditions for accepted combinations of empty and non-empty required data fields are detailed for each moduled are outlined in page 9 of the [EV-ChART Data Preparation and Guidance](https://driveelectric.gov/files/ev-chart-data-guidance.pdf)
- Essentially AsyncBizMagic has 2 main processes
    - Validation: Validate that data uploads meets the conditions detailed in the EV-ChART Data and Preparation Guidance for allowable combinations of empty and non-empty required fields
    - Transformation: Convert all empty and non-empty data into correct datatypes against the fields outlined in the database for that module table

### Current Biz Magic Process from an Application Architecture Perspective
1. Previous process of AsyncDataValidation passes and triggers AsyncBizMagic lambda function to run
2. Retrieve uploaded CSV data from S3 bucket
3. If validation/transformation rules are applicable for the module being uploaded
    - Apply row-level business validation for empty and non-empty data
    - Convert data into acceptable datatypes expected for that module table in the database
4. Save as JSON file to S3 bucket
5. Sends SNS message to queue under biz-magic: pass or fail
    - If it passes: send file-type in SNS message: JSON, trigger AsyncValidatedUpload, and insert the data from the JSON file into the module table in the database
    - If it fails: the errors found during validation is inserted into an error table, an error report JSON file is created for the upload_id, and the module validation process terminates

### How to Add a New Validation/Transformation to AsyncBizMagic
1. Developer should update the field's column definitions in ```database_central_config.json``` for desired module
    - If a field is required, developer should update the ```module_validation``` dictionary and set ```required``` to True
    - Example of ```module_validation``` for the ```port_id``` field in ```module2_data_v3``` table in ```database_central_config.json```
    ```
        "module_validation": {
          "default": {
            "required": true,
            "datatype": "string",
            "max_length": 36
          }
        }
    ```
    - If a field is required and the field is allowed to be empty, as similarly outlined in page 9 of the [EV-ChART Data Preparation and Guidance](https://driveelectric.gov/files/ev-chart-data-guidance.pdf), developer should update the ```module_validation``` and set ```required``` and ```required_empty_allowed``` to True
    - ```required_empty_allowed``` should be set to True if the current field is required, but can be submitted as an empty value when no relevant data can be given for a reporting period
    ```
        "module_validation": {
            "default": {
                "required": true,
                "datatype": "string",
                "max_length": 36,
                "required_empty_allowed": true
            }
        }
    ```
2. If there isn’t currently a validation file for the specific module named ```validation_m#``` in ```lambda_layers/python/module_validation```, developer should create a validation script
    - Some modules do not have their own validation script because no further data validation checks are needed after a module's datatype has been verified by column
    - A validation script is necessary when row validation is needed
        - This file will include methods that ensure that the combination of data in the row is valid based on its context, while also sending a proper error message if validation fails
    - Examples include:
        - Checking that a row of data is a valid empty row, or otherwise includes all required data
            - This check is in place for Modules 2, 4, 5 & 9
        - Ensuring that station timestamps happen after a station's operational_date
            - This check is in place for non-empty Module 3 data
        - Checking that a field that stores a total of other fields is accurate (i.e. total cost = federal costs + other costs)
            - This is potential method implementation that further demonstrates how the validation file can be utilized to validate business logic
    - The most common use case for having a validation and transformation functions is when modules are allowed to be submitted with empty values or empty rows
        - This process is currently implemented for Modules 2, 3, 4 & 9
        - In these scenarios, validation checks are applied to ensure that expected fields are left empty, and transformation methods are applied to convert the empty fields into None datatype to comply with expected database datatypes

3. If there isn’t currently a transformation file for the specific module named ```transform_m#``` in ```lambda_layers/python/module_transform```, developer should create a transformation script
    - This is where any method that deals with changing the form of data goes
    - The data must be transformed to comply with the expected datatypes outlined for that field in the database
    - Examples include:
        - Converting empty data into None datatype so that the field can be recorded accurately when inserting into the database
            - Module 2 Example: ```energy_kwh``` is a required decimal field that is allowed to be empty along with other required fields as specified on page 9 of the [EV-ChART Data Preparation and Guidance](https://driveelectric.gov/files/ev-chart-data-guidance.pdf). When a valid empty row is being processed, the ```validate_empty_session()``` in the ```transform_m2.py``` will convert the empty string value to ```None``` so that it will be inserted into the database as a ```Null``` value. If it is left as an empty string, an error will be thrown during insertion
        - Converting other datatypes into decimals, booleans, timestamps etc.
            - Module 4 Example:
                - For a non-empty valid row of data, the ```allow_null_outages()``` in ```transform_m4.py``` converts the ```outage_id``` and ```outage_duration``` fields into datetime objects in ISO 8601 format. If it is left unconverted, an error will be thrown during insertion
4. Developer must update the ```AsyncBizMagic``` script, specifically the ```custom_validations``` and ```custom_transformation``` dictionaries and specify the validation or transformation methods recently created in the lambda_layers folder that are required for each module
    - Snippet of the ```custom_validations``` and ```custom_transformations``` dictionaries declared in ```AsyncBizMagic```:
    ```
    custom_validations = {
        2: [validate_m2.validate_empty_session],
        3: [validate_m3.validate_operational_one_year],
        4: [validate_m4.validate_empty_outage],
        5: [],
        6: [],
        7: [],
        8: [],
        9: [validate_m9.validate_empty_capital_install_costs],
    }

    custom_transformations = {
        2: [transform_m2.allow_null_charging_sessions],
        3: [transform_m3.allow_null_uptime],
        4: [transform_m4.allow_null_outages],
        5: [transform_m5.allow_null_federal_maintenance],
        6: [],
        7: [],
        8: [],
        9: [transform_m9.allow_null_capital_install_costs],
    }
    ```
5. Developers should always update the respective unit test script for each API as they make modifications to the API script
    - For adjustments to the ```APIGetSubmittingNullData```, the test script can be found under the test folder following the same file structure of their source API script. For example, source script is ```source\lambda_functions\APIGetSubmittingNullData\index.py``` and test script will be in ```tests\source\lambda_functions\APIGetSubmittingNullData\test_api_get_submitting_null_data.py```
    - For new validation methods, find the respective test file under ```tests\source\lambda_layers\python\module_validation\test_module_#...```. Write new tests for valid and invalid workflows of the new methods. Include all potential variations of valid and invalid data to ensure that actual behavior matches expected behavior
    - For new transform methods, find the respective test file under ```tests\source\lambda_layers\python\module_transform\test_module_#.py```. Write new tests for valid and invalid workflows of the new methods

### How to Run Unit Tests against AsyncBizMagic
1. In order to test out complete functionality of ```AsyncBizMagic``` (file retrieval, validation and transformation, and error insertion), unit tests are created under ```tests\source\lambda_functions\AsyncBizMagic\test_async_biz_magic.py```
    - The csv module file that will go through the biz magic checks should be put in the ```./tests/sample_data/``` folder
    - In order to imitate the way AsyncBizMagic retrieves the csv file from the AWS S3 bucket, the unit tests mock out the S3 bucket and hard code the file path and upload key
2. Developer must declare and hard code a new ```UPLOAD_KEY_``` and ```UPLOAD_FILE_PATH_``` variable at the top of the file, ensuring that the ```UPLOAD_FILE_PATH_``` is a valid, existing file path leading to the csv data intended for testing. These constants will be used when mocking out the S3 bucket (see step 3 for instructions on how to mock out S3 bucket)
    - ```UPLOAD_KEY_``` is used to reference the correct mocked bucket, but can be hardcoded to any random, unique value
    - ```UPLOAD_FILE_PATH_``` must be accurate since the test will try and reference the actual csv file
3. Developer must then mock out a new S3 bucket within the ```s3_client``` fixture
    - Copy and paste an existing mocked S3 bucket inside ```fixture_s3_client()``` and update the ```UPLOAD_FILE_PATH``` and ```UPLOAD_KEY``` to the variables declared in step 2
    - Example of mocked bucket:

    ```
        conn.Bucket(UPLOAD_BUCKET_NAME).put_object(
            Key=UPLOAD_KEY,
            Body=get_file_content(UPLOAD_FILE_PATH),
            Metadata={
                "checksum": UPLOAD_CHECKSUM,
                "recipient_type": "direct-recipient"
            },
        )
    ```
4. In the actual unit test, developer must mock the return value of other functions that gather information about the upload such as: ```get_active_feature_toggles()```, ```get_org_info_dynamo()```, ```get_upload_metadata()```
    - Example:
    ```
        mock_get_active_feature_toggles.return_value = {Feature.BIZ_MAGIC}
        mock_get_org_info.return_value = {"name": "Org Name"}
        mock_get_upload_metadata.return_value = get_upload_id_metadata()
    ```
5. Utilize the helper function ```get_event_object()``` with the ```UPLOAD_KEY_``` as a parameter in order to get the event object needed to successfully run AsyncBizMagic
    - Example:
    ```
        event_object = get_event_object(UPLOAD_KEY)
        api_response = async_biz_magic(event_object, None)
    ```
6. If a file not found error occurs, double check that the ```UPLOAD_KEY_``` is referenced correctly in the mocked S3 bucket
7. Correctly setting up the S3 bucket, mocking out other helper functions, and passing in the correct event object will allow the unit test to execute AsyncBizMagic properly