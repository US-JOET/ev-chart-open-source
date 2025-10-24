subrecip_submit_deny = """
Hello {sr_first_name},
<br><br>
Module {module_number}: {module_name}, a {reporting_period} submission for the year {reporting_year}, was <strong>rejected</strong> by {dr_org_name} and is NOT considered submitted.
<br>
<dl>
    <dt><strong>Step 1</strong></dt>
    <dd>Review the {dr_org_name} feedback about the rejected module data.</dd>
    <dt><strong>Step 2</strong></dt>
    <dd>Address the feedback left by the {dr_org_name} reviewer and correct any errors as needed.</dd>
    <dt><strong>Step 3</strong></dt>
    <dd>Upload a new module data file for submission. Once uploaded and submitted to {dr_org_name} for approval, {dr_org_name} will review and approve/reject the new file.</dd>
</dl>
<br><br>
<table>
    <tr>
        <th colspan="2"> {reporting_year} Module {module_number}: {module_name} </th>
    </tr>
    <tr>
        <td>Decision</td>
        <td><strong>Rejected</strong></td>
    </tr>
    <tr>
        <td>Decision Date</td>
        <td><strong>{decision_date}</strong></td>
    </tr>
    <tr>
        <td>Reviewed By</td>
        <td><strong>{dr_name}</strong></td>
    </tr>
    <tr>
        <td>Feedback from Reviewer</td>
        <td><strong>{feedback}</strong></td>
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
        <td>{module_last_updated_on}</td>
    </tr>
    <tr>
        <td>Updated By</td>
        <td>{module_last_updated_by}</td>
    </tr>
    <tr>
        <td>Upload ID</td>
        <td>{upload_id}</td>
    </tr>
</table><br>
<br>
<a href="https://evchart.driveelectric.gov/login">Login to EV-ChART</a> to review the rejected module’s feedback. <br><br>
"""


subrecip_submit_deny_multi_body = """
<table>
    <tr>
        <th colspan="2"> Direct Recipient Feedback </th>
    </tr>
    <tr>
        <td>Decision</td>
        <td><strong>Rejected</strong></td> 
    </tr>
    <tr>
        <td>Decision Date</td>
        <td><strong>{decision_date}</strong></td>
    </tr>
    <tr>
        <td>Reviewed By</td>
        <td><strong>{dr_name}</strong></td>
    </tr>
    <tr>
        <td>Feedback from Reviewer</td>
        <td><strong>{feedback}</strong></td>
    </tr>
</table><br>
<table>
    <tr>
        <th colspan="2">Module Details</th>
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
        <td>Feedback from Reviewer</td>
        <td><strong>{feedback}</strong></td>
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
        <td>{module_last_updated_on}</td>
    </tr>
    <tr>
        <td>Updated By</td>
        <td>{module_last_updated_by}</td>
    </tr>
    <tr>
        <td>Upload ID</td>
        <td>{upload_id}</td>
    </tr>
</table>
"""
