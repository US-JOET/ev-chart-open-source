## Contents
- [Python local testing setup](#python-local-testing-setup)
- [Pylint](#pylint)
- [How to Connect to Aurora](#how-to-connect-to-aurora)
- [How to Add a New Environment](#how-to-add-a-new-environment)

## Python local testing setup
### Create a virtual env
command line
The python will be based on the version that you have installed as "python". \
If you have multiple versions installed you can use the install path instead of the keyword
```
# Create .venv dir
python -m venv ./.venv

# Activate using powershell
.venv\Scripts\Activate.ps1
# Activate using cmd
.venv\Scripts\activate.bat

#Install the test requirements
pip install -r .\tests\requirements.txt
```
VSCode:
https://code.visualstudio.com/docs/python/environments

### Run Tests
command line
```
python -m pytest -s ./tests
```
VSCode: https://code.visualstudio.com/docs/python/testing#_configure-tests

## Pylint
### How to run
Command line
```
#requirements
pip install pylint
#running for a specific directory
pylint <dir(source and tests for example)>
```

VSCode

Download the Pylint extension \
To force scan click ctrl+shift+p then select "Pylint:Restart Server" \
You can view issues in the Problems \
If something should not trigger a problem you can disable scan for that line by adding # pylint: disable=name-of-issue at the end of line \
If something should not trigger a problem for the whole project you can add it to the .pylintrc disable list

### Formatter
PEP8 https://peps.python.org/pep-0008/

VSCode: comes with Black so that is what I am currently using.  If you want to use it outside VSCode you need to pip install it \
To run Black, right click on the file and click Format file or
```
shift + alt + f
```

Pycharm : https://blog.jetbrains.com/pycharm/2023/07/2023-2-eap-5/

## CodeQL
### Setup
1. go to https://github.com/github/codeql-cli-binaries/releases
2. download the package for your platform
3. extract to a directory of your choice (not the project dir)
4. add the directory to your systems PATH so you can run codeql
5. create a codeql database
```
codeql database create path/todatabase --language=javascript --source-root path/to/your/project
```
```
codeql database create path/todatabase --language=python --source-root path/to/your/project
```

### Run
```
codeql query run path/to/code/ql/query/pack --database path/to/database
```
## Bandit (Security checks)
### Setup
```
pip install bandit
```

### Run
```
bandit -r path/to/code
```
For example:
```
cd source/lambda_functions
bandit -r ./
```

## Code Coverage (python tests)
### setup
```
pip install coverage
```
### run
```
coverage run -m pytest .\tests\
```
then get report
```
coverage report -m
```
this can be exported to a text file via '> coverage.txt' at the end of the report line

## ESLint (frontend linter)
### Setup (should be able to skip if you just install dev)
first time setup (already done)
```
npm install --save-dev eslint eslint-plugin-react eslint-plugin-react-hooks globals @eslint/js typescript-eslint eslint-plugin-import
```
or
```
npm install --dev
```
### Run
```
npx eslint path/to/code
```
For example:
```
npx eslint ./frontend
```
or
```
npm run lint
```

fix specific file
```
npx eslint path/to/code --fix
```

## Prettier (frontend formatter)
### Setup (should be able to skip if you just install dev)
first time setup (already done)
```
npm install --save-dev prettier
```
or
```
npm install --dev
```
### Run
to check file
```
npx prettier --check path/to/file
```

to format
```
npx prettier --write path/to/code
```

VSCode: use the prettier extension

## ESLint + Prettier
### Setup (should be able to skip if you just install dev)
first time setup (already done)
```
npm install --save-dev eslint-config-prettier eslint-plugin-prettier
```
or
```
npm install --dev
```
### Run
```
npm run lint
```
VSCode: eslint-prettier extension check config to point it at the one we are using

## How to Connect to Aurora

1. Create a new Lambda function in the EV-ChART development account with a unique name.
   1. Proceed with the default choice `Author from scratch`.
   1. Chose the latest Python runtime.
   1. Expand `Change default execution role`.
      1. Choose `Use an existing role`.
      1. Chose the existing role that is prefixed with `LambdaExecution-Nevi...`.
   1. Click `Create function`.

1. Add the `AWSSDKPandas-Python3xx` function layer.
   1. In the new function, scroll down to the bottom of the Console and click the `Add a layer` button for the `Layers` header to the right.
   1. Proceed with the default `Layer source`: `AWS layers`.
   1. Choose `AWSSDKPandas-Python3xx` (`xx` being the latest supported Python minor version) for the `AWS layers` dropdown.
   1. Choose the only version available for `Version`.
   1. Click `Add`.

1. Add the `EV-ChART_Python_Layer` function layer.
   1. Reopen the Lambda layer configuration page.
   1. Select `Custom layers` for `Layer source`.
   1. Choose the layer that is prefixed with `EV-ChART_Python_Layer...` for the `Custom layers` dropdown.
   1. Choose the only version available for `Version`.
   1. Click `Add`.

1. Increase the function timeout.
   1. In the new function, select the `Configuration` tab.
   1. Select `General configuration` in the left navigation.
   1. Click the `Edit` button for the `General configuration` header to the right.
   1. Increase the function timeout to something higher than the default 3 seconds.
      - 30 seconds is a good number.
   1. Click `Save`.

1. Associate to the account VPC.
   1. In the new function, select the `Configuration` tab.
   1. Select `VPC` in the left navigation.
   1. Click the `Edit` button for the `VPC` box or header to the right.
   1. Select the only available VPC: `vpc-05a349f3444076a6d`.
   1. Select a subnet in the `172.28.7.0/24` CIDR address space.
   1. Select the security group with ID `sg-033d88f0ef1672caa`.
   1. Click `Save`.
      - It can take some time before the Lambda function will execute successfully after this change.

1. Update the function code to connect to Aurora.
   1. Import:
      ```
      from evchart_helper import aurora
      ```
   1. Utilize your `aurora` variable to establish a database connection and use as you would with any `pymysql` connection.
      ```
      connection = aurora.get_connection()
      cursor = connection.cursor()
      cursor.execute("""
        SELECT @@version
      """, [])
      output = cursor.fetchall()
      connection.commit() # Remember to commit if adding data to the database.
      ```
   1. When done, close the connection:
      ```
      aurora.close_connection()
      ```
      Or:
      ```
      connection.close()
      ```
   1. For ease of management, set up the `connection` and `cursor` using `with`:
      ```
      with (
        aurora.get_connection() as connection,
        connection.cursor() as cursor
      ):
        cursor.execute("""
          SELECT @@version
        """, [])
        output = cursor.fetchall()
        connection.commit()
      ```
      This removes the need to explicitly close the connection as it will be done automatically.  The imported `aurora` will clean up itself as needed.

## How to Add a New Environment
1. Determine the environment moniker (e.g. `qa`, `preprod`) and which primary environment (`dev`, `test`, or `prod`) it will be related to.
    - **Replace all instances of `MONIKER` in the subsequent instructions with the identified new environment moniker.**
1. Make a new repository branch that will be identified as managing the new environment.
1. Create a new deployment configuration for that moniker.
    1. Copy the baseline configuration (`devops/baseline.configuration.json`) and rename the new file `baseline.MONIKER.configuration.json`.
        - Edit the new file with the below content:
            ```
            [
                { "ParameterKey": "SubEnvironment", "ParameterValue": "MONIKER" }
            ]
            ```
    1. Copy the configuration of the related primary environment (e.g. `devops/deploy.dev.configuration.json`) and rename the new file `deploy.MONIKER.configuration.json`.
        - Edit the new file and add the below to the list of parameters:
            ```
                { "ParameterKey": "SubEnvironment", "ParameterValue": "MONIKER" }
            ```
            **Ensure commas are added as necessary for valid JSON structure.**
1. Create a new deployment workflow for that moniker.
    1. Copy the workflow of the related primary environment (e.g. `.github/workflows/develop_deploy.yaml`) and rename the new file `MONIKER_deploy.yaml`.
        - Edit the new file making the below changes:
            - Set the `on.push.branches` list to contain only the name of the new environment branch.
                - Only if the primary environment is not `prod`.
            - Set `name` to `deploy MONIKER`.
            - Set `jobs.environment-restrictions.environment` to the environment moniker.
            - Set `jobs.get-sha.steps.0.with.ref` to the name of the new environment branch.
            - Set `jobs.trigger-tests.with.BRANCH_NAME` to the name of the new environment branch.
            - Set `jobs.trigger-deploy.with.ENV_NAME` to the environment moniker.
            - Set `jobs.trigger-deploy.with.BRANCH_NAME` to the name of the new environment branch.

        **This new workflow file will need to be present on the default repository branch (`develop`) before workflows can be run manually.**
1. Create a new React configuration for that moniker.
    1. Copy the configuration of the related primary environment (e.g. `frontend/.env.dev`) and rename the new file `.env.MONIKER`.
        - Edit the new file making the below changes:
            - Set `PUBLIC_URL` and `REACT_APP_API_URL` to the identified hostname (generally `https://evchart-MONIKER.driveelectric.gov`) for the new environment.
            - Take note of `REACT_APP_CLIENTID`; this value will need to be revisited in a future step.
    1. Edit `frontend/package.json` and add the below to the `scripts` attribute:
        ```
            "build:MONIKER": "env-cmd -f .env.MONIKER react-scripts build"
        ```
        **Ensure commas are added as necessary for valid JSON structure.**
1. Deploy the new environment.
    1. Access the relevant AWS account and identify the new AWS Cognito user pool client; take note of the client ID.
    1. Update the value for `REACT_APP_CLIENTID` in the React configuration for the new environment.


## Useful testing suggestions
1.  with no way to test sql when creating your query you can unit test using cursor.mogrify()
    1. to set this up in the test use the following
    ```
    from pymysql.connections import Connection
    conn = Connection(
        host="localhost", user="fake", password="fake", database="fake", defer_connect=True
    )
    conn.encoding = "utf8mb4"
    conn.client_flag = 0
    conn.server_status = 0
    conn._sock = True

    cursor = connection.cursor()
    ```
    instead of executing the query use 
    ```
    cursor.mogrify(query=query, args=data)
    ```