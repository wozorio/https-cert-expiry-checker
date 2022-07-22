import argparse
import requests
from urllib.request import ssl, socket
import datetime
import smtplib
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from python_http_client.exceptions import HTTPError


def check_url(url: str):
    try:
        response = requests.get('https://' + url, allow_redirects=True)
    except requests.exceptions.RequestException as error:
        raise SystemExit(error)


def get_days_before_expiration(url: str, port: int = 443):
    context = ssl.create_default_context()

    with socket.create_connection((url, port)) as sock:
        with context.wrap_socket(sock, server_hostname=url) as ssock:
            certificate = ssock.getpeercert()

            certificate_expiration_date = datetime.datetime.strptime(
                certificate['notAfter'], '%b %d %H:%M:%S %Y %Z')

            days_before_certificate_expires = (
                certificate_expiration_date - datetime.datetime.now()).days

            return days_before_certificate_expires


def send_mail(url: str, sender: str, recipient: str, sendgrid_api_key: str, days_before_certificate_expires: int):
    email_api = 'https://api.sendgrid.com/v3/mail/send'
    subject = 'TLS certificate for', url, 'about to expire'

    print('INFO: Sending notification via e-mail')

    message = Mail(
        from_email=sender,
        to_emails=recipient,
        subject=subject,
        html_content=f'<p> Dear Site Reliability Engineer, </p> \
        <p> This is to notify you that the TLS certificate for <b>{url}</b> is expiring soon. </p> \
        <p> Please ensure a new certificate is ordered and installed in a timely fashion. There are {days_before_certificate_expires} days remaining. </p> \
        <p> Sincerely yours, <br>DevOps Team </p>')

    try:
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        print(response.status_code, response.body, response.headers)
    except HTTPError as error:
        print(error.to_dict)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-u', '--url', type=str, required=True)
    parser.add_argument('-s', '--sender', type=str, required=True)
    parser.add_argument('-r', '--recipient', type=str, required=True)
    parser.add_argument('-k', '--sendgrid_api_key', type=str, required=True)
    parser.add_argument('-t', '--thresold', type=int, default=60)

    args = parser.parse_args()

    check_url(args.url)

    days_before_certificate_expires = get_days_before_expiration(args.url)

    if days_before_certificate_expires <= args.thresold:
        print('WARN: The TLS certificate for', args.url, 'will expire in',
              days_before_certificate_expires, 'days')

        send_mail(args.url, args.sender,
                  args.recipient, args.sendgrid_api_key, days_before_certificate_expires)

    print('INFO: Nothing to worry about. The TLS certificate for', args.url,
          'will expire only in', days_before_certificate_expires, 'days')
