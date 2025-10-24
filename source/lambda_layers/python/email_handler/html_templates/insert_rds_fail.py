insert_rds_fail = """
Hello {first_name}, <br><br>

Due to a system error, Module {module_number} ({module_name}) for the year {reporting_year} failed to 
be inserted into the EV-ChART database. Complete the following steps to correct
the error. We apologize for any inconvenience.<br><br>

<strong>Step 1</strong><br>
Contact EV-ChART Tech Support <br><br>

<strong>Step 2</strong><br>
Select "Reporting (EV-ChART)" as the Inquiry Type <br><br>

<strong>Step 3</strong><br>
Send message including the error type </q>Failed Inserting to Database</q> <br><br>

<strong>Step 4</strong><br>
Work with EV-ChART Team to identify and correct the error <br><br>

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