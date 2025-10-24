"""
EmailSender

The hander that consumes the email SQS queue and sends the email request to the DOE Proofpoint
server.
"""
import smtplib
import re
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email import utils
from evchart_helper.custom_logging import LogEvent
from evchart_helper.custom_exceptions import EvChartEmailError

def handler(event, context):
    sender_email = 'EV-ChART No-Reply <evchart-noreply@ee.doe.gov>'
    records_email = 'EV-ChART Records <evchart-records@ee.doe.gov>'
    environment = os.environ.get('ENVIRONMENT', "N/A").upper()
    log = LogEvent({}, api="EmailSender", action_type="READ")

    for record in event['Records']:
        receiver_email = record['messageAttributes']['receiver_email']['stringValue']
        subject = record['messageAttributes']['email_subject']['stringValue']
        #message_plain = str(record['messageAttributes']['plain_text']['stringValue'])
        message_html = str(record['body'])

        receiver_email = re.sub('\+(.*?)\@','@', receiver_email) #Change address if contains + as proofpoint can't handle them
        message_header = '***This is an automatically generated email, please do not reply to this message. \
            For questions, <a href="https://driveelectric.gov/contact/?inquiry=evchart">contact us</a>.*** <br><br>'
        message_html = '<style>table, th, td {border: 1px solid black;border-collapse: collapse;}</style>' + \
            message_header + message_html
        message_html = message_html + '<img src="cid:logosignature" alt="Ev-ChART Logo" height="20" style="margin-right: 100px;"/><br>'
        message_html = message_html + '<img src="cid:joetsignature" alt="JOET Logo" height="30"/>'

        message = MIMEMultipart("alternative")
        message["Subject"] = get_subject_by_env(subject, environment)
        message["From"] = sender_email
        message["To"] = receiver_email
        message['Date'] = utils.formatdate(localtime = 1)
        message.attach(MIMEText(message_html, "html"))
        #message.attach(MIMEText(message_plain, "plain"))

        if(subject.endswith("Failed Data Processing")):
            with open('errorgraphic.png', 'rb') as fp:
                message_graphic = MIMEImage(fp.read(), 'png')
            message_graphic.add_header('Content-ID', '<errorgraphic>')
            message_graphic.add_header('Content-Disposition', 'attachment', filename='errorgraphic.png')
            message.attach(message_graphic)

        if(subject.endswith("added as a user in EV-ChART")):
            with open("rolegraphic.png", "rb") as fp:
                message_graphic = MIMEImage(fp.read(), "png")
            message_graphic.add_header("Content-ID", "<rolegraphic>")
            message_graphic.add_header("Content-Disposition", "attachment", filename="rolegraphic.png")
            message.attach(message_graphic)

        with open('evchartlogo.png', 'rb') as fp: #Read image
            message_sign = MIMEImage(fp.read(), 'png')
        # Define the image's ID as referenced above
        message_sign.add_header('Content-ID', '<logosignature>')
        message_sign.add_header('Content-Disposition', 'attachment', filename='evchartlogo.png')
        message.attach(message_sign)
        with open('joetlogo.png', 'rb') as fp: #Read image
            message_sign = MIMEImage(fp.read(), 'png')
        # Define the image's ID as referenced above
        message_sign.add_header('Content-ID', '<joetsignature>')
        message_sign.add_header('Content-Disposition', 'attachment', filename='joetlogo.png')
        message.attach(message_sign)

        try:
            server = smtplib.SMTP('mxrelay.doe.gov', 25, timeout=10)
            server.set_debuglevel(1)
            server.sendmail(sender_email, [receiver_email] + [records_email], message.as_string())
            server.quit()
        except TimeoutError as e:
            raise EvChartEmailError(log_obj=log, message=f"Error thrown in EmailSender: {e}")
        except smtplib.SMTPConnectError as e:
            raise EvChartEmailError(log_obj=log, message=f"Error thrown in EmailSender: {e}")
        except OSError as e:
            raise EvChartEmailError(log_obj=log, message=f"Error thrown in EmailSender: Connection timed out. SMTP server may be temporarily unavailable: {e}")

def get_subject_by_env(subject, environment):
    return subject if environment == "PROD" else f"[{environment}] {subject}"
