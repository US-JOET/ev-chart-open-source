"""
APIDefault

Functionally, the Web server for the application.  This function will accept any path requests not
explicitly defined in the API Gateway and return the React application from S3 (or other static
assets such as images/JavaScript/stylesheets/etc.) with simple caching functionality.  Additional
functionality includes session cookie checking, forcing redirects to /login when appropriate.
"""
import base64
import json
import logging
import os
from pathlib import Path, PurePath
import re

from evchart_helper.boto3_manager import boto3_manager
from evchart_helper.cognito import cognito
from evchart_helper.session import SessionManager

s3_client = boto3_manager.client("s3")
ssm_client = boto3_manager.client("ssm")

logger = logging.getLogger("APIDefault")
logger.setLevel(logging.DEBUG)


def get_file(static_bucket, path, is_binary_file):
    ct_mapping = {
        "css": "text/css",
        "html" : "text/html",
        "jpg": "image/jpeg",
        "js": "text/javascript",
        "json": "application/json",
        "map": "application/json",
        "png": "image/x-png",
        "svg": "image/svg+xml",
        "txt": "text/plain",
        "ttf": "font/ttf",
        "woff2": "font/woff2"
    }

    local_path = Path(f"/tmp{path}") # nosec - JE-5399
    if not Path.is_file(local_path):
        local_path.parent.mkdir(parents=True, exist_ok=True)
        s3_client.download_file(static_bucket, str(PurePath(f"deploy/react{path}")), local_path)

    with open(local_path, mode=f"r{'b' if is_binary_file else ''}") as f: # pylint: disable=unspecified-encoding
        file = {
            "Body": f.read(),
            "ContentType": ct_mapping[path.rsplit(".", maxsplit=1)[-1]]
        }

    return file


def get_static_bucket():
    sub_environment = os.environ.get("SUBENVIRONMENT")
    sub_environment_path = f"/{sub_environment}" if sub_environment else ""

    return ssm_client.get_parameter(
        Name=f"/ev-chart/s3{sub_environment_path}/static-asset-bucket-name"
    )["Parameter"]["Value"]


def cookie_path_check(event_path, path):
    return event_path != "/" and event_path.is_relative_to(PurePath(path))


def handler(event, _context): # pylint: disable=too-many-locals
    log_data = {
        "headers": event.get("headers"),
        "path": event["path"]
    }

    static_bucket = get_static_bucket()

    # For an SPA, paths (without files) determine application content; understand this and instead
    # use "/index.html" for requests that are just paths and not URIs to specific files.
    event_path = PurePath(event["path"])
    path_dir = str(event_path.parent if event_path.suffix else event_path)
    s3_path_dir = str(event_path.parent) if event_path.suffix else ""
    file = event_path.name if event_path.suffix else "index.html"
    file_extension = PurePath(file).suffix[1:]

    ignore_cookie_paths = ("/manifest.json", "/login", "/static")
    ignore_cookie = any(
        cookie_path_check(event_path, path)
        for path in ignore_cookie_paths
    )

    if not ignore_cookie:
        event_cookies = event["headers"].get("Cookie", "") or event["headers"].get("cookie", "")
        user_session = SessionManager(event_cookies)

        if not user_session.get_session_id():
            logger.debug(json.dumps(log_data))

            return {
                "headers": {
                    "Location": "/login"
                },
                "statusCode": 302
            }

        log_data |= {
            "session_user": user_session.identifier,
            "session_valid": user_session.session_valid
        }

        if not user_session.session_valid:
            logger.debug(json.dumps(log_data))

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

    # Binary content needs to be handled differently due to limitations with API Gateway.  For this
    # content, issue a permanent redirect so API Gateway can handle the request properly by using a
    # specific path that features the file extension.
    if path_dir == "/static/media":
        logger.debug(json.dumps(log_data))

        return {
            "headers": {
                "Location": f"{path_dir}/{file_extension}/{file}"
            },
            "statusCode": 301
        }

    # Catch requests from that temporary redirect path and remove the added file extension part.
    # The path structure does not change in S3 so its removal is required as the code is still using
    # the original "real" path to locate the relevant file.
    if path_dir == f"/static/media/{file_extension}":
        s3_path_dir = s3_path_dir.replace(f"/{file_extension}", "")

    response = {
        "headers": {
            "Content-Type": "text/html"
        }
    }

    is_binary_file = any(file_type in file_extension for file_type in [
        "jpg", "png", "svg", "ttf", "woff2"
    ])

    try:
        file_data = get_file(
            static_bucket,
            f"{s3_path_dir}/{file}",
            is_binary_file
        )
        file_body = file_data["Body"]

    except s3_client.exceptions.ClientError as e:
        logger.debug(json.dumps(log_data | {"message": str(e)}))

        status_code = re.search(r"\d{3}", str(e))
        message = str(e).rsplit(": ", maxsplit=1)[-1]

        response["body"] = message
        response["statusCode"] = status_code.group()

    except Exception as e: # pylint: disable=broad-exception-caught
        logger.debug(json.dumps(log_data | {"message": str(e)}))

        response["body"] = "Invalid request."
        response["statusCode"] = 403

    else:
        # Binary content is just encoded into base64 and only that data is returned to the API
        # Gateway for specific handling.
        if is_binary_file:
            logger.debug(json.dumps(log_data))

            return base64.b64encode(file_body).decode("utf-8")

        response["body"] = file_body
        response["headers"] = {
            "Content-Type": file_data["ContentType"]
        }
        response["statusCode"] = 200

    logger.debug(json.dumps(log_data))
    return response
