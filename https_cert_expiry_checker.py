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
# ]
# ///

# pylint: disable=missing-module-docstring

__author__ = "Wellington Ozorio <wozorio@duck.com>"

import dataclasses
import datetime
import logging
import os
from urllib.request import socket, ssl

import click
import requests
from colorlog import ColoredFormatter
from python_http_client.exceptions import HTTPError
from sendgrid import SendGridAPIClient, SendGridException
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Email:
    """Represent the properties of an email."""

    sender: str
    recipients: list[str]
    subject: str


def parse_recipients(value: str) -> list[str]:
    """Click custom parameter type to parse a comma-separated string into a list of recipients."""
    return value.split(",")


@click.command()
@click.argument("url")
@click.argument("sender")
@click.argument("recipients", type=parse_recipients)
@click.option("--threshold", default=60, type=int, help="days before expiry to notify (default: 60)")
def main(url: str, sender: str, recipients: list[str], threshold: int) -> None:
    """Check the expiration date of HTTPS/SSL certificates and notify engineers
    in case the expiration date is less than the `threshold` argument in days.
    """
    setup_logging()

    check_sendgrid_api_key_env_var()

    check_url(url)

    cert_expiry_date = get_cert_expiry_date(url)
    days_before_cert_expires = get_days_before_cert_expires(cert_expiry_date)

    if days_before_cert_expires > threshold:
        logger.info(
            "Nothing to worry about. The TLS certificate for %s will expire only in %i days",
            url,
            days_before_cert_expires,
        )
        return

    logger.warning("The TLS certificate for %s will expire in %i days", url, days_before_cert_expires)

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


def check_sendgrid_api_key_env_var() -> None:
    """Check whether the environment variable with Sendgrid API key is set."""
    if not os.getenv("SENDGRID_API_KEY"):
        raise RuntimeError("SENDGRID_API_KEY environment variable is not set")


def check_url(url: str) -> None:
    """Validate the provided URL."""
    try:
        requests.get("https://" + url, allow_redirects=True, timeout=5)
    except requests.exceptions.RequestException as error:
        logger.exception(error)


def get_cert_expiry_date(url: str, port: int = 443) -> datetime.datetime:
    """Get the expiration date of the SSL certificate."""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((url, port)) as sock:
            with context.wrap_socket(sock, server_hostname=url) as ssock:
                cert = ssock.getpeercert()
                return datetime.datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(
                    tzinfo=datetime.timezone.utc
                )
    except socket.error as error:
        raise RuntimeError(f"Failed to retrieve certificate from {url}") from error


def get_days_before_cert_expires(cert_expiry_date: datetime.datetime) -> int:
    """Return the amount of days remaining before the certificate expires."""
    return int((cert_expiry_date - datetime.datetime.now(datetime.timezone.utc)).days)


def send_email(url: str, email: Email, cert_expiry_date: datetime.datetime, days_before_cert_expires: int) -> None:
    """Send notification email through SendGrid API."""
    message = Mail(
        from_email=email.sender,
        to_emails=email.recipients,
        subject=email.subject,
        html_content=set_email_content(url, cert_expiry_date, days_before_cert_expires),
    )
    try:
        logger.info("Sending notification via e-mail")
        sendgrid = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sendgrid.send(message)
        logger.info("Email sent successfully (status code: %i)", response.status_code)
    except (HTTPError, SendGridException) as error:
        logger.exception(error)


def set_email_content(url: str, cert_expiry_date: datetime.datetime, days_before_cert_expires: int) -> str:
    """Set the content in HTML of the email to be sent out."""
    return f"""<p>Dear Site Reliability Engineer,</p>
    <p>This is to notify you that the TLS certificate for <b>{url}</b> will expire on {cert_expiry_date}.</p>
    <p>Please, ensure that the certificate is renewed in a timely fashion.
    There are {days_before_cert_expires} days remaining.</p>
    <p>Sincerely yours,</p>
    <p>DevOps Team</p>"""


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
