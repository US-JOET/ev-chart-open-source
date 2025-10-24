dr_review_sr_station = """
Hello {first_name},
<p>
A charging station has been added in EV-ChART by {sr_org_name} for {dr_org_name}. The station is now "Pending" and requires review.
<p>
<strong>Step 1</strong><br>
Review the details of the station that is "Pending."
<p>
<strong>Step 2</strong><br>
If the station information is correct, select approve to complete the station registration process. If the station information is incorrect, either edit the station details or reject* the station.
<p>
*If rejected, the station will not be added to EV-ChART and {sr_org_name} or {dr_org_name} will need to add a new station for it to be registered in EV-ChART.
<p>
<table>
    <tr>
        <th colspan="2">Sample Station Details - View Complete Details in App</th>
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
        <td>Address</td>
        <td><strong>{station_address}<br>{station_city}, {station_state} {station_zip}-{station_zip_extended}</strong></td>
    </tr>
    <tr>
        <td>Network Provider</td>
        <td><strong>{station_np}</strong></td>
    </tr>
    <tr>
        <td>Funding Type</td>
        <td><strong>{station_funding_type}</strong></td>
    </tr>
    <tr>
        <td>On AFC</td>
        <td><strong>{station_afc}</strong></td>
    </tr>
    <tr>
        <td>Number of Federally-Funded Ports</td>
        <td><strong>{ports_num_fed}</strong></td>
    </tr>
    <tr>
        <td>Authorized Subrecipient(s)</td>
        <td><strong>{sr_org_name}</strong></td>
    </tr>
</table>
<p>
<a href="https://evchart.driveelectric.gov/login">Login to EV-ChART</a> to review the complete station information that is pending.
<p>
"""
