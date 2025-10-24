station_authorizes_subrecipient = """
Hello {sr_first_name},<br><br>

{sr_org_name} has been authorized to submit data on behalf of {dr_org_name} for the 
following station:
<ul>
    <li>Station ID: <strong>{station_id}</strong></li>
    <li>Station Nickname for Station {station_id} created by {dr_org_name}: <strong>{station_nickname}</strong></li>
</ul> <br>

<a href="https://evchart.driveelectric.gov/login">Login to EV-ChART</a> to 
start uploading data for this station.  <br><br>

"""