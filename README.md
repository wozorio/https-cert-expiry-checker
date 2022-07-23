<div align="center">
    <p>
        <img alt="Python Logo" src="img/circle-python.svg?sanitize=true" width="75" />
    </p>
</div>

# HTTPS Certificate Expiry Checker

[![GitHub](https://img.shields.io/github/license/wozorio/https-cert-expiry-checker)](https://github.com/wozorio/https-cert-expiry-checker/blob/master/LICENSE)

A Python script that checks the expiration date of HTTPS/TLS certificates and notifies engineers in case the expiration date is less than the `threshold` in days.

## Prerequisites

```bash
$ sudo ./install-requirements.sh
```

## Usage

```
$ ./https-cert-expiry-checker.py --help
usage: https-cert-expiry-checker.py [-h] -u URL -s SENDER -r RECIPIENT
                                    [RECIPIENT ...] -k SENDGRID_API_KEY
                                    [-t THRESHOLD]

optional arguments:
  -h, --help            show this help message and exit
  -t THRESHOLD, --threshold THRESHOLD
                        Number of days to be notified before the certificate
                        expires. When omitted, a value of 60 is used

required arguments:
  -u URL, --url URL     URL to be checked
  -s SENDER, --sender SENDER
                        Sender e-mail address
  -r RECIPIENT [RECIPIENT ...], --recipient RECIPIENT [RECIPIENT ...]
                        Recipients e-mail addresses
  -k SENDGRID_API_KEY, --sendgrid_api_key SENDGRID_API_KEY
                        SendGrid API key
```
