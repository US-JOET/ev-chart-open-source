"""
APILogout

[Unused, TODO: Implement] As part of logging out of the application, this function will do some
additional housekeeping to clear out any data related to the active session.
"""
import json
import logging
import os
import urllib3

from evchart_helper.cognito import cognito
from evchart_helper.session import SessionManager

if os.environ.get("NETWORKPROXY"):
    http = urllib3.ProxyManager(
        os.environ["NETWORKPROXY"],
        ca_certs=f"/opt{os.environ['NETWORKPROXYCERT']}" if os.environ.get("NETWORKPROXYCERT") else None
    )
else:
    http = urllib3.PoolManager()

logger = logging.getLogger("APILogout")
logger.setLevel(logging.DEBUG)


def revoke_refresh_token(refresh_token):
    if not refresh_token:
        return

    cognito_response = http.request(
        "POST",
        (
            f"https://{cognito.domain}"
            f".auth-fips.{os.environ['AWS_REGION']}.amazoncognito.com/oauth2/revoke"
        ),
        body=f"token={refresh_token}",
        headers={
            "Authorization": f"Basic {cognito.get_basic_auth_string()}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )

    if cognito_response.status != 200:
        logger.debug(json.dumps({
            "message": cognito_response.data,
            "status": cognito_response.status
        }))


def handler(event, _context):
    log_data = {
        "headers": event.get("headers")
    }

    event_cookies = event["headers"].get("Cookie", "") or event["headers"].get("cookie", "")
    user_session = SessionManager(event_cookies)

    log_data |= {
        "session_user": user_session.identifier,
        "session_valid": user_session.session_valid
    }

    logger.debug(json.dumps(log_data))

    if not user_session.session_valid:
        return {
            "headers": {
                "Location": "/"
            },
            "statusCode": 302
        }

    revoke_refresh_token(user_session.refresh_token)

    user_session.clear_session()
    return {
        "headers": {
            "Location": (
                f"https://{cognito.domain}"
                f".auth-fips.{os.environ['AWS_REGION']}.amazoncognito.com/logout"
                f"?client_id={cognito.client_id}"
                f"&logout_uri={cognito.logout_urls[0]}"
            ),
            "Set-Cookie": (
                "__Host-session_id=; Path=/; SameSite=Strict; Secure; HttpOnly"
            )
        },
        "statusCode": 302
    }
