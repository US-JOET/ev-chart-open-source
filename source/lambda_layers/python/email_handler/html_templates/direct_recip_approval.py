direct_recip_approval = """
Hello {first_name}, <br><br>

Module {module_number} ({module_name}) for the year {reporting_year} was submitted by 
{sr_org_name}, is now "Pending Approval", and requires review. <br><br>

<strong>Step 1</strong><br>
Review the module data that is pending approval. <br><br>

<strong>Step 2</strong><br>
 Select the approve or reject* button to complete the submission process.<br>
 *If rejected, {sr_org_name} or {dr_org_name} will need to upload a new file for submission.
<br><br>

<table>
    <tr>
        <th colspan="2">Pending Approval - Module Details</th>
    </tr>
    <tr>
        <td>Module</td>
        <td><strong>Module {module_number}: {module_name}</strong></td> 
    </tr>
    <tr>
        <td>Reporting Year</td>
        <td><strong>{reporting_year}</strong></td>
    </tr>
    <tr>
        <td>Type</td>
        <td><strong>{reporting_period}</strong></td>
    </tr>
    <tr>
        <td>Direct Recipient</td>
        <td><strong>{dr_org_name}</strong></td>
    </tr>
    <tr>
        <td>Subrecipient/Contractor</td>
        <td><strong>{sr_org_name}</strong></td>
    </tr>
    <tr>
        <td>Updated On</td>
        <td>{last_updated_on}</td>
    </tr>
    <tr>
        <td>Updated By</td>
        <td>{last_updated_by}</td>
    </tr>
    <tr>
        <td>Upload ID</td>
        <td>{upload_id}</td>
    </tr>
</table><br><br>

<a href="https://evchart.driveelectric.gov/login">Login to EV-ChART</a> to review the module that is pending approval.  <br><br>


"""
direct_recip_approval_multi_body = """
<br><br>
<table>
    <tr>
        <th colspan="2">Pending Approval - Module Details</th>
    </tr>
    <tr>
        <td>Module</td>
        <td><strong>Module {module_number}: {module_name}</strong></td> 
    </tr>
    <tr>
        <td>Reporting Year</td>
        <td><strong>{reporting_year}</strong></td>
    </tr>
    <tr>
        <td>Type</td>
        <td><strong>{reporting_period}</strong></td>
    </tr>
    <tr>
        <td>Direct Recipient</td>
        <td><strong>{dr_org_name}</strong></td>
    </tr>
    <tr>
        <td>Subrecipient/Contractor</td>
        <td><strong>{sr_org_name}</strong></td>
    </tr>
    <tr>
        <td>Updated On</td>
        <td>{last_updated_on}</td>
    </tr>
    <tr>
        <td>Updated By</td>
        <td>{last_updated_by}</td>
    </tr>
    <tr>
        <td>Upload ID</td>
        <td>{upload_id}</td>
    </tr>
</table>
"""
