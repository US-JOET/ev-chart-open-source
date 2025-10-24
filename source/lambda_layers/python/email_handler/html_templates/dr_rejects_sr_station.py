def get_funding_status_section(
    station_is_federally_funded, station_funding_type, station_project_type
):
    funding_type_row = ""
    is_federally_funded = "NO"
    if station_is_federally_funded == 1:
        funding_type_row = f"""
        <tr>
            <td>Funding Type</td>
            <td><strong>{station_funding_type}</strong></td>
        </tr>"""
        is_federally_funded = "YES"

    return f"""
    <table>
        <tr>
            <th colspan="2">Part 2: Federal Funding Status</th>
        </tr>
        <tr>
            <td>Federally Funded</td>
            <td><strong>{is_federally_funded}</strong></td>
        </tr>
        {funding_type_row}
        <tr>
            <td>Project Type</td>
            <td><strong>{station_project_type}</strong></td>
        </tr>
    </table>"""


dr_rejects_sr_station = """
Hello {first_name},
<p>
The following station has been <strong>rejected</strong> by {dr_org_name} and was <strong>not added</strong> to EV-ChART.
<p>
<ul>
    <li>Station Nickname: <strong>{station_nickname}</strong></li>
    <li>Station ID: <strong>{station_id}</strong></li>
</ul>
<p>
<table>
    <tr>
        <th colspan="2">Rejection Details</th>
    </tr>
    <tr>
        <td>Decision</td>
        <td><strong>Rejected</strong></td>
    </tr>
    <tr>
        <td>Decision Date</td>
        <td><strong>{updated_on}</strong></td>
    </tr>
    <tr>
        <td>Reviewed By</td>
        <td><strong>{updated_by}</strong></td>
    </tr>
    <tr>
        <td>Direct Recipient</td>
        <td><strong>{dr_org_name}</strong></td>
    </tr>
    <tr>
        <td>Feedback from Reviewer</td>
        <td><strong>{feedback}</strong></td>
    </tr>
</table>
<p>
<strong>Step 1</strong><br>
Review {dr_org_name}'s feedback (in the table above) to understand their reasons for rejection.
<p>
<strong>Step 2</strong><br>
Address the feedback and create a new station using the "Add Station" form and the updated station information.
<p>
<strong>Step 3</strong><br>
Once the new station is submitted to {dr_org_name} for approval, {dr_org_name} will review the new station. Once approved, you will be notified by email and can start uploading data for that station on behalf of the {dr_org_name}.
<p>
<a href="https://evchart.driveelectric.gov/login">Login to EV-ChART</a> to address the feedback and create a new station using the "Add Station" form.
<p>
<strong>Station Not Added to EV-ChART</strong>
<table>
    <tr>
        <th colspan="2">Part 1: Station Profile</th>
    </tr>
    <tr>
        <td>Station Nickname</td>
        <td><strong>{station_nickname}</strong></td>
    </tr>
    <tr>
        <td>Station ID</td>
        <td><strong>{station_id}</strong></td>
    </tr>
    <tr>
        <td>Station Address</td>
        <td><strong>{station_address}</strong></td>
    </tr>
    <tr>
        <td>Station City</td>
        <td><strong>{station_city}</strong></td>
    </tr>
    <tr>
        <td>Station State</td>
        <td><strong>{station_state}</strong></td>
    </tr>
    <tr>
        <td>Station ZIP</td>
        <td><strong>{station_zip}</strong></td>
    </tr>
    <tr>
        <td>Station ZIP Extended</td>
        <td><strong>{station_zip_extended}</strong></td>
    </tr>
    <tr>
        <td>Station Lattitude</td>
        <td><strong>{station_lat}</strong></td>
    </tr>
    <tr>
        <td>Station Longitude</td>
        <td><strong>{station_long}</strong></td>
    </tr>
    <tr>
        <td>Network Provider</td>
        <td><strong>{station_np}</strong></td>
    </tr>
    <tr>
        <td>Operational Date</td>
        <td><strong>{station_operational_date}</strong></td>
    </tr>
    <tr>
        <td>Station Located on AFC</td>
        <td><strong>{station_afc}</strong></td>
    </tr>
</table>
<br>
{funding_status_section}
<br>
<table>
    <tr>
        <th colspan="2">Part 3: Authorize Subrecipient(s)/Contractor(s)</th>
    </tr>
    <tr>
        <td>Authorized Subrecipient(s)</td>
        <td><strong>{sr_org_name}</strong></td>
    </tr>
</table>
<br>
<table>
    <tr>
        <th colspan="2">Part 4: Port Information</th>
    </tr>
    <tr>
        <td>Number of Federally Funded Ports</td>
        <td><strong>{ports_num_fed}</strong></td>
    </tr>
    <tr>
        <td>Number of Non- Federally Funded Ports</td>
        <td><strong>{ports_num_non_fed}</strong></td>
    </tr>
    {fed_port_table}
</table>
<br>
"""
