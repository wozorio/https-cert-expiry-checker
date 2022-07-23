#!/usr/bin/env python3

import argparse
import requests
import datetime
import smtplib

from urllib.request import ssl, socket
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from python_http_client.exceptions import HTTPError


def check_url(url: str):
    try:
        resp = requests.get('https://' + url, allow_redirects=True)
    except requests.exceptions.RequestException as err:
        raise SystemExit(err)


def get_days_before_cert_expires(url: str, port: int = 443):
    context = ssl.create_default_context()

    with socket.create_connection((url, port)) as sock:
        with context.wrap_socket(sock, server_hostname=url) as ssock:
            cert = ssock.getpeercert()

            cert_expiry_date = datetime.datetime.strptime(
                cert['notAfter'], '%b %d %H:%M:%S %Y %Z')

            days_before_cert_expires = (
                cert_expiry_date - datetime.datetime.now()).days

            return days_before_cert_expires


def send_mail(url: str, sender: str, recipients: list, sendgrid_api_key: str, days_before_cert_expires: int):
    email_api = 'https://api.sendgrid.com/v3/mail/send'
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
        sg = SendGridAPIClient(sendgrid_api_key)
        resp = sg.send(message)
        print(resp.status_code, resp.body, resp.headers)
    except HTTPError as err:
        print(err.to_dict)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-u', '--url',
        help='<Required> URL to be checked',
        type=str,
        required=True)
    parser.add_argument(
        '-s', '--sender',
        help='<Required> Sender e-mail address',
        type=str,
        required=True)
    parser.add_argument(
        '-r', '--recipient',
        help='<Required> Recipients e-mail addresses',
        nargs='+',
        type=str,
        required=True)
    parser.add_argument(
        '-k', '--sendgrid_api_key',
        help='<Required> SendGrid API key',
        type=str,
        required=True)
    parser.add_argument(
        '-t', '--threshold',
        help='<Optional> Number of days to be notified before certificate expires',
        type=int,
        default=60)

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
