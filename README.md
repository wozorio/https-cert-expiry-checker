<div align="center">
    <p>
        <img alt="Python Logo" src="img/circle-python.svg?sanitize=true" width="75" />
    </p>
</div>

# HTTPS Certificate Expiry Checker

[![GitHub](https://img.shields.io/github/license/wozorio/https-cert-expiry-checker)](https://github.com/wozorio/https-cert-expiry-checker/blob/main/LICENSE)
[![CI](https://github.com/wozorio/https-cert-expiry-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/wozorio/https-cert-expiry-checker/actions/workflows/ci.yml)

A Python script that checks the expiration date of HTTPS/TLS certificates and notifies engineers in case the expiration date is less than the `threshold` in days.

## Prerequisites

1. Set an environment variable with the SendGrid API key:
    ```bash
    $ export SENDGRID_API_KEY=<SENDGRID_API_KEY>
    ```

1. Install requirements:

    ```bash
    $ sudo ./install-requirements.sh
    ```

## Usage

```
$ ./https_cert_expiry_checker.py --help
usage: https_cert_expiry_checker.py [-h] -u URL -s SENDER -r RECIPIENTS [RECIPIENTS ...] [-t THRESHOLD] [-v]

options:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit

required arguments:
  -u URL, --url URL     URL to be checked
  -s SENDER, --sender SENDER
                        sender e-mail address
  -r RECIPIENTS [RECIPIENTS ...], --recipients RECIPIENTS [RECIPIENTS ...]
                        recipients e-mail addresses

optional arguments:
  -t THRESHOLD, --threshold THRESHOLD
                        number of days to be notified before the certificate expires (default: 60)

```
