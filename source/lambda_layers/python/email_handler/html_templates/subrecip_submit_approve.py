subrecip_submit_approve = """
Hello {sr_first_name},
<br><br>
Module {module_number}: {module_name}, a {reporting_period} submission for the year {reporting_year}, was <strong>approved</strong> by {dr_org_name} and, in doing so, is now submitted.
 No further actions are needed to complete this submission.<br>

<table>
    <tr>
        <th colspan="2"> {reporting_year} Module {module_number}: {module_name} </th>
    </tr>
    <tr>
        <td>Decision</td>
        <td><strong>Approved</strong></td>
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
Thank you for reporting data to EV-ChART!<br><br>
"""

subrecip_submit_approve_multi_body = """
<table>
    <tr>
        <th colspan="2"> Direct Recipient Feedback </th>
    </tr>
    <tr>
        <td>Decision</td>
        <td><strong>Approved</strong></td>
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
</table><br>
Thank you for reporting data to EV-ChART!<br><br>
"""
