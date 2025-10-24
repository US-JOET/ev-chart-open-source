data_processing_success = """
Hello {first_name}, <br><br>

Module {module_number} ({module_name}) for the year {reporting_year} was successfully 
uploaded to EV-ChART. <strong>This upload is now considered a draft</strong> that is ready to submit. <br><br>

<table>
    <tr>
        <th colspan="2">{reporting_year} Module {module_number}: {module_name}</th>
    </tr>
    <tr>
        <td>Upload Status</td>
        <td><strong>Draft</strong></td> 
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
</table>  <br><br>

<a href="https://evchart.driveelectric.gov/login">Login to EV-ChART</a>
 to complete the submission of this module.

 <br><br>
"""

s2s_processing_success = """
Hello {first_name}, <br><br>

Module {module_number} ({module_name}) for the year {reporting_year} was successfully 
uploaded to EV-ChART. This upload is now <strong>Pending Approval</strong> by {dr_name} <br><br>

<table>
    <tr>
        <th colspan="2">{reporting_year} Module {module_number}: {module_name}</th>
    </tr>
    <tr>
        <td>Upload Status</td>
        <td><strong>Pending Approval</strong></td> 
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
</table>  <br><br>

 <br><br>
"""
