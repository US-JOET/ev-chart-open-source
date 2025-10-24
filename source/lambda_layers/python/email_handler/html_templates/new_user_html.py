new_user_html = """
Hello {first_name},
<p>
Welcome to EV-ChART, the Electric Vehicle Charging Analytics and Reporting Tool! You have been added
as a {org_name} {role} in EV-ChART by a member of your organization.  To understand what you have access to as an EV-ChART {role}, review the attached checklist.<br><br>
<strong>How do I sign in?</strong><br>
When signing into EV-ChART for the first time, follow the steps below:<br><br>
<strong>1. Create a login.gov user account</strong>, which is required to sign into EV-ChART
<ul padding="0"; margin="0">
    <li>Use this <a href="https://login.gov/help/get-started/create-your-account/">step-by-step guide</a> to create a login.gov user</li>
    <li>For more info, you may also visit:<ul>
                <li><a href="https://login.gov/help/get-started/authentication-methods/">Authentication methods | Login.gov</a></li>
                <li><a href="https://login.gov/help/trouble-signing-in/how-to-sign-in/">How to sign in to Login.gov | Login.gov</a></li>
        </ul>
    </li>
</ul>

<strong>2. Sign in</strong> to EV-ChART at <a href="https://evchart.driveelectric.gov/login">https://evchart.driveelectric.gov/login</a>
<ul>
    <li>Select “Sign in with OneID”</li>
    <li>Select “LOGIN.GOV” and sign in with your login.gov credentials </li>
</ul>

<strong>Have questions?</strong>
<ul>
        <li>Please use this <a href="https://driveelectric.gov/contact/?inquiry=evchart">Contact Us form</a> to notify our Tech Support Team of any questions/tech challenges. We will work on responding and troubleshooting any issues right away.</li>
</ul>

<strong>Additional resources:</strong>
<ul>
    <li>View the <a href="https://driveelectric.gov/evchart-user-guide">EV-ChART User Manual</a> to support you in navigating the data submission process</li>
    <li>View the <a href="https://driveelectric.gov/files/ev-chart-data-guidance.pdf">Data Format and Preparation Guidance</a> which gives a detailed explanation of the data definitions</li>
    <li>Download the <a href="https://driveelectric.gov/files/ev-chart-data-input-template.xlsx">Excel Input Template</a> which is how the data will need to be submitted as a CSV</li>
</ul>

Thanks for plugging in,<br><br>
"""
