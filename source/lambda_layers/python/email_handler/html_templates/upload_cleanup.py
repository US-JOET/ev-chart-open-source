upload_cleanup = """
Hello {first_name},
<br><br>
EV-ChART has identified the following uploads <strong>contain no data</strong>:
<br>
<table>
    <tr>
        <th> Upload ID </th>
        <th> Module </th>
        <th> Reporting Year </th>
        <th> Quarter (if applicable) </th>
        <th> Direct Recipient </th>
        <th> Updated On </th>
    <tr>
    {combined_table}
</table>    
<br>
Once daily, <strong>EV-ChART will automatically delete stale uploads</strong> which do not contain any data. 
<br>
<strong>Have questions or concerns?</strong>
<a href="https://driveelectric.gov/contact">Contact us</a>, with the Inquiry Type selected as ‘Reporting (EV-ChART),’ to notify our Tech Support Team of your question or issue. 
We will respond and troubleshoot any issues promptly.
<br>
"""

table_item = """
<tr>
    <td>{upload_id}</td>
    <td>{module_number}</td>
    <td>{reporting_year}</td>
    <td>{quarter}</td>
    <td>{dr_name}</td>
    <td>{updated_on}</td>
</tr>"""