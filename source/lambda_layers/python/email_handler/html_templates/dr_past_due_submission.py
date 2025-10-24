dr_past_due_submission = """

Hello {first_name},  
<br><br>
{dr_org_name} is not in compliance with <a href="https://www.ecfr.gov/current/title-23/chapter-I/subchapter-G/part-680/section-680.112">23 CFR 680.112</a> and has <strong>not submitted all of the required modules to EV-ChART for the {reporting_period} {year}</strong> reporting period.
<br><br>
Please <a href="https://evchart.driveelectric.gov/login">Login to EV-ChART</a> and upload data for the following stations and modules:
<br>
<br>
<ul>
    {station_list}
</ul>
<br>
Here are some <u>additional resources</u> to support you in completing your data submission:
<br>
<ul>
    <li>Use the homepage Submission Tracker to track each stations' progress towards having all modules submitted on time.</li>
    <li>Sign in to EV-ChART at <a href="https://evchart.driveelectric.gov/login">https://evchart.driveelectric.gov/login</a></li>
    <li>View the <a href="https://driveelectric.gov/evchart-user-guide">EV-ChART User Guide</a></li>
    <li>View the <a href="https://driveelectric.gov/files/ev-chart-data-guidance.pdf">Data Format and Preparation Guidance</a> which gives a detailed explanation of the data definitions</li>
    <li>Download the <a href="https://driveelectric.gov/files/ev-chart-data-input-template.xlsx">Excel Input Template</a> which is how the data will need to be submitted as a CSV</li>
</ul>
<br>
<strong>Have questions or concerns?</strong>
<br>
<a href="https://driveelectric.gov/contact/?inquiry=evchart">Contact us</a>, with the Inquiry Type selected as ‘Reporting (EV-ChART),’ to notify our Tech Support Team of your issue. We will respond and troubleshoot any issues right away.  
<br>
Thanks for plugging in,
<br>
"""

stations_list_item = """
<li>Station Nickname: Station ID - {station_name}: {station_id}</li>
{authorized_sr_section}
<ul>
    <li>Module(s) overdue:</li>
    <ul>
        {overdue_module_list}
    </ul>
</ul>
"""


authorized_sr_present = """
<ul>
   <li>Authorized subrecipient(s)/contractor(s):</li>
    <ul>
        {sr_list}
    </ul>
</ul>
"""

sr_list_item = """
<li>{sr_name}</li>
"""

overdue_module_item = """
<li>Module {mod_id}: {module_name}</li>
"""
