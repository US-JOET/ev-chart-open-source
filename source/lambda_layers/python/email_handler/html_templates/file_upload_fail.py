file_upload_fail = """
Hello {first_name}, <br><br>

Due to a system error, Module {module_number} ({module_name}) for the year {reporting_year} failed to upload
to EV-ChART. Complete the following steps to correct the error. We apologize for any 
inconvenience. <br><br>

<strong>Step 1</strong>
Login to EV-ChART <br><br>

<strong>Step 2</strong>
Retry uploading the module data file. If the error persists, please contact us. <br><br>

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
<br><br>
"""