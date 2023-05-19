#!/usr/bin/env python3

"""HTTPS Certificate Expiry Checker

A script to check the expiration date of HTTPS/SSL certificates and notify
engineers in case the expiration date is less than the threshold in days.
"""

__version__ = "0.0.1"
__author__ = "Wellington Ozorio <well.ozorio@gmail.com>"

import argparse
import datetime
import logging as logger
import os
import sys
from urllib.request import socket, ssl

import requests
from python_http_client.exceptions import HTTPError
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def main() -> None:
    """The main function."""
    args = get_args()
    check_sendgrid_api_key_env_var()

    email = {"sender": args.sender, "recipients": args.recipients}
    check_url(args.url)

    cert_expiry_date = get_cert_expiry_date(args.url)
    days_before_cert_expires = get_days_before_cert_expires(cert_expiry_date)

    if days_before_cert_expires < args.threshold:
        log(f"WARN: The TLS certificate for {args.url} will expire in " f"{days_before_cert_expires} days")
        send_mail(args.url, email, cert_expiry_date, days_before_cert_expires)
    else:
        log(
            f"INFO: Nothing to worry about. The TLS certificate for {args.url} "
            f"will expire only in {days_before_cert_expires} days"
        )


def get_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()

    required_arg = parser.add_argument_group("required arguments")
    optional_arg = parser.add_argument_group("optional arguments")

    required_arg.add_argument("-u", "--url", help="URL to be checked", type=str, dest="url", required=True)
    required_arg.add_argument("-s", "--sender", help="sender e-mail address", type=str, dest="sender", required=True)
    required_arg.add_argument(
        "-r", "--recipients", help="recipients e-mail addresses", nargs="+", type=str, dest="recipients", required=True
    )
    optional_arg.add_argument(
        "-t",
        "--threshold",
        help="number of days to be notified before the certificate expires (default: 60)",
        type=int,
        dest="threshold",
        default=60,
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s version {__version__}")

    args = parser.parse_args()

    return args


def check_sendgrid_api_key_env_var() -> None:
    """Check whether the environment variable with Sendgrid API key is set."""
    if not os.getenv("SENDGRID_API_KEY"):
        log("ERROR: SENDGRID_API_KEY environment variable is not set")
        raise RuntimeError


def check_url(url: str) -> None:
    """Validate the provided URL."""
    try:
        requests.get("https://" + url, allow_redirects=True, timeout=5)
    except requests.exceptions.RequestException as error:
        logger.exception(error)
        sys.exit(1)


def get_cert_expiry_date(url: str, port: int = 443) -> datetime:
    """Get the expiration date of the SSL certificate."""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((url, port)) as sock:
            with context.wrap_socket(sock, server_hostname=url) as ssock:
                cert = ssock.getpeercert()
                cert_expiry_date = datetime.datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
    except socket.error as error:
        logger.exception(error)
        sys.exit(1)

    return cert_expiry_date


def get_days_before_cert_expires(cert_expiry_date: datetime.date) -> int:
    """Return the amount of days remaining before the certificate expires."""
    return int((cert_expiry_date - datetime.datetime.now()).days)


def send_mail(url: str, email: dict, cert_expiry_date: datetime.date, days_before_cert_expires: int) -> None:
    """Send notification email through SendGrid API."""
    log("INFO: Sending notification via e-mail")
    message = Mail(
        from_email=email["sender"],
        to_emails=email["recipients"],
        subject=f"TLS certificate for {url} about to expire",
        html_content=f"""<p> Dear Site Reliability Engineer, </p> \
            <p> This is to notify you that the TLS certificate for <b>{url}</b> will expire on {cert_expiry_date}. </p> \
            <p> Please ensure a new certificate is ordered and installed in a timely fashion. There are {days_before_cert_expires} days remaining. </p> \
            <p> Sincerely yours, <br>DevOps Team </p>
            """,
    )
    try:
        sendgrid = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sendgrid.send(message)
        log(f"Response code: {response.status_code}\nResponse body: {response.body}\nResponse headers: {response.headers}")
    except HTTPError as error:
        logger.exception(error)
        sys.exit(1)


def log(msg: str) -> None:
    """Wrapper to log messages to stderr."""
    print(msg, file=sys.stderr)


if __name__ == "__main__":
    main()
