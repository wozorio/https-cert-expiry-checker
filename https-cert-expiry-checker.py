#!/usr/bin/env python3

""""
HTTPS Certificate Expiry Checker
"""

import argparse
import datetime
from urllib.request import ssl, socket

import requests
from python_http_client.exceptions import HTTPError

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

__author__ = 'Wellington Ozorio'
__email__ = 'well.ozorio@gmail.com'
__version__ = '0.0.1'


def check_url(url: str):
    try:
        requests.get('https://' + url, allow_redirects=True)
    except requests.exceptions.RequestException as err:
        raise SystemExit(err)


def get_days_before_cert_expires(url: str, port: int = 443) -> int:
    context = ssl.create_default_context()

    with socket.create_connection((url, port)) as sock:
        with context.wrap_socket(sock, server_hostname=url) as ssock:
            cert = ssock.getpeercert()

            cert_expiry_date = datetime.datetime.strptime(
                cert['notAfter'], '%b %d %H:%M:%S %Y %Z')

            days_before_cert_expires = (
                cert_expiry_date - datetime.datetime.now()).days

            return days_before_cert_expires


def send_mail(url: str, sender: str, recipients: list,
              sendgrid_api_key: str, days_before_cert_expires: int):
    subject = f'TLS certificate for {url} about to expire'

    print('INFO: Sending notification via e-mail')

    message = Mail(
        from_email=sender,
        to_emails=recipients,
        subject=subject,
        html_content=f'<p> Dear Site Reliability Engineer, </p> \
        <p> This is to notify you that the TLS certificate for <b>{url}</b> is expiring soon. </p> \
        <p> Please ensure a new certificate is ordered and installed in a timely fashion. There are {days_before_cert_expires} days remaining. </p> \
        <p> Sincerely yours, <br>DevOps Team </p>')

    try:
        sendgrid = SendGridAPIClient(sendgrid_api_key)
        resp = sendgrid.send(message)
        print(resp.status_code, resp.body, resp.headers)
    except HTTPError as err:
        print(err.to_dict)


def get_args():
    parser = argparse.ArgumentParser()

    required_arg = parser.add_argument_group('required arguments')

    required_arg.add_argument(
        '-u', '--url',
        help='URL to be checked',
        type=str,
        required=True)
    required_arg.add_argument(
        '-s', '--sender',
        help='Sender e-mail address',
        type=str,
        required=True)
    required_arg.add_argument(
        '-r', '--recipient',
        help='Recipients e-mail addresses',
        nargs='+',
        type=str,
        required=True)
    required_arg.add_argument(
        '-k', '--sendgrid_api_key',
        help='SendGrid API key',
        type=str,
        required=True)
    parser.add_argument(
        '-t', '--threshold',
        help='Number of days to be notified before the certificate expires. When omitted, a value of 60 is used',
        type=int,
        default=60)
    parser.add_argument(
        '-v', '--version',
        action="version",
        version=f"%(prog)s version {__version__} by {__author__}")

    return parser


def main():
    parser = get_args()

    args = parser.parse_args()

    check_url(args.url)

    days_before_cert_expires = get_days_before_cert_expires(args.url)

    if days_before_cert_expires <= args.threshold:
        print('WARN: The TLS certificate for', args.url, 'will expire in',
              days_before_cert_expires, 'days')

        send_mail(args.url, args.sender,
                  args.recipient, args.sendgrid_api_key, days_before_cert_expires)
    else:
        print('INFO: Nothing to worry about. The TLS certificate for', args.url,
              'will expire only in', days_before_cert_expires, 'days')


if __name__ == "__main__":
    main()
