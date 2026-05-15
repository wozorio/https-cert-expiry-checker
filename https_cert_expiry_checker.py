#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click",
#     "colorlog",
#     "python-http-client",
#     "requests",
#     "sendgrid",
#     "jinja2",
# ]
# ///

# pylint: disable=missing-module-docstring

__author__ = "Wellington Ozorio <wozorio@duck.com>"

import dataclasses
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from urllib.request import socket, ssl

import click
import requests
from colorlog import ColoredFormatter
from jinja2 import Template
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

EMAIL_ADDRESS_PATTERN = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

EMAIL_TEMPLATE = Template("""
<p>Dear Site Reliability Engineer,</p>
<p>This is to notify you that the TLS certificate for <b>{{ url }}</b> is expiring on {{ cert_expiry_date }}.</p>
<p>Please, ensure that the certificate is renewed in a timely fashion.
There are {{ days_before_cert_expires }} days remaining.</p>
<p>Sincerely yours,</p>
<p>DevOps Team</p>
""")

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Email:
    """Represent the properties of an email."""

    sender: str
    recipients: list[str]
    subject: str


def validate_email_addresses(value: str) -> list[str]:
    """Click custom parameter type to validate the format of provided email addresses."""
    emails = value.split(",")
    for email in emails:
        validate_email_address(email)
    return emails


@click.command()
@click.argument("url")
@click.argument("sender")
@click.argument("recipients", type=validate_email_addresses)
@click.option("--threshold", default=60, type=int, help="days before expiry to notify (default: 60)")
def main(url: str, sender: str, recipients: list[str], threshold: int) -> None:
    """Check the expiration date of HTTPS/SSL certificates and notify engineers
    in case the expiration date is less than the `threshold` argument in days.
    """
    setup_logging()

    validate_email_address(sender)

    check_sendgrid_api_key_env_var()

    check_url(url)

    now = datetime.now(tz=timezone.utc)
    cert_expiry_date = get_cert_expiry_date(url)
    days_before_cert_expires = (cert_expiry_date - now).days

    if (cert_expiry_date - now) > timedelta(days=threshold):
        logger.info(
            "Nothing to worry about. The TLS certificate for %s is expiring only in %i days",
            url,
            days_before_cert_expires,
        )
        return

    logger.warning("The TLS certificate for %s is expiring in %i days", url, days_before_cert_expires)

    send_email(
        url,
        Email(sender=sender, recipients=recipients, subject=f"TLS certificate for {url} about to expire"),
        cert_expiry_date,
        days_before_cert_expires,
    )


def setup_logging() -> None:
    """Set up a custom logger."""
    handler = logging.StreamHandler()
    formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s %(levelname)-8s%(reset)s %(white)s%(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",  # ISO-8601 format
        reset=True,
        log_colors={"DEBUG": "cyan", "INFO": "green", "WARNING": "yellow", "ERROR": "red"},
        style="%",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel("INFO")


def validate_email_address(email_address: str) -> None:
    """Validate whether an email address has a valid format."""
    match = EMAIL_ADDRESS_PATTERN.match(email_address)

    if not match:
        raise ValueError(f"Email address format {email_address} is not valid")


def check_sendgrid_api_key_env_var() -> None:
    """Check whether the environment variable with Sendgrid API key is set."""
    if not os.getenv("SENDGRID_API_KEY"):
        raise RuntimeError("SENDGRID_API_KEY environment variable is not set")


def check_url(url: str) -> None:
    """Check the provided URL."""
    response = requests.get("https://" + url, allow_redirects=True, timeout=5)
    response.raise_for_status()


def get_cert_expiry_date(url: str, port: int = 443) -> datetime:
    """Get the expiration date of the SSL certificate."""
    context = ssl.create_default_context()
    with socket.create_connection((url, port)) as sock:
        with context.wrap_socket(sock, server_hostname=url) as ssock:
            cert = ssock.getpeercert()
            return datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)


def send_email(url: str, email: Email, cert_expiry_date: datetime, days_before_cert_expires: int) -> None:
    """Send notification email through SendGrid API."""
    logger.info("Sending notification via e-mail")
    message = Mail(
        from_email=email.sender,
        to_emails=email.recipients,
        subject=email.subject,
        html_content=set_email_content(url, cert_expiry_date, days_before_cert_expires),
    )
    sendgrid = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
    response = sendgrid.send(message)
    logger.info("Email sent successfully (status code: %i)", response.status_code)


def set_email_content(url: str, cert_expiry_date: datetime, days_before_cert_expires: int) -> str:
    """Set the content in HTML of the email to be sent out."""
    return EMAIL_TEMPLATE.render(
        url=url,
        cert_expiry_date=cert_expiry_date,
        days_before_cert_expires=days_before_cert_expires,
    )


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
