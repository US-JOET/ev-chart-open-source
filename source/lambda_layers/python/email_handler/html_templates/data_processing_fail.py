data_processing_fail = """
Hello {first_name}, <br><br>

Module {module_number} {module_name} for the year {reporting_year} failed a data 
processing check. Complete the following steps to correct identified errors and 
re-upload the data module. <br><br>

<strong>Step 1</strong> <br>
<a href="https://evchart.driveelectric.gov/login">Login to EV-ChART</a> <br><br>

<strong>Step 2</strong> <br>
Navigate to the module data file with the "Error" status. Select "Actions" and then 
"Download Error Report." <br><br>

<strong>Step 3</strong> <br>
Within the Error Report, expand Column E and read each error description. <br><br>

<strong>Step 4</strong> <br>
Correct the identified errors in the module data file. <br><br>

<strong>Step 5</strong> <br>
Upload a new data module file. <br><br>

<table>
    <tr>
        <th colspan="2">{reporting_year} Module {module_number}: {module_name}</th>
    </tr>
    <tr>
        <td>Upload Status</td>
        <td><strong>Error</strong></td> 
    </tr>
        <tr>
        <td>Direct Recipient</td>
        <td><strong>{dr_name}</strong></td> 
    </tr>
        <tr>
        <td>Subrecipient/Contractor</td>
        <td><strong>{sr_name}</strong></td> 
    </tr>
        <tr>
        <td>Updated On</td>
        <td>{updated_on}</td> 
    </tr>
        <tr>
        <td>Updated By</td>
        <td>{updated_by}</td> 
    </tr>
        <tr>
        <td>Upload ID</td>
        <td>{upload_id}</td> 
    </tr>
</table>
<br><img src="cid:errorgraphic" alt="Ev-ChART Error report Guidence Graphic" height="600" style="margin-right: 100px;"/>
<br>
"""
