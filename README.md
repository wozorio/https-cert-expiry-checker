# HTTPS Certificate Expiry Checker

[![GitHub](https://img.shields.io/github/license/wozorio/https-cert-expiry-checker)](https://github.com/wozorio/https-cert-expiry-checker/blob/main/LICENSE)
[![CI](https://github.com/wozorio/https-cert-expiry-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/wozorio/https-cert-expiry-checker/actions/workflows/ci.yml)

<div align="center">
    <p>
        <img alt="Python Logo" src="img/logo.png?sanitize=true" width="150" />
    </p>
</div>

## Description

A Python script that checks the expiration date of HTTPS/TLS certificates and notifies engineers in case the expiration date is less than the `threshold` in days.

## Getting Started

### Prerequisites

Set an environment variable with the SendGrid API key:

```bash
export SENDGRID_API_KEY=<SENDGRID_API_KEY>
```

### Usage

```bash
./https_cert_expiry_checker.py --help
Usage: https_cert_expiry_checker.py [OPTIONS] URL SENDER

  Check the expiration date of HTTPS/SSL certificates and notify engineers in
  case the expiration date is less than the `threshold` argument in days.

Options:
  --version                Show the version and exit.
  -r, --recipients TEXT    recipient email addresses  [required]
  -t, --threshold INTEGER  days before expiry to notify (default: 60)
  --help                   Show this message and exit.
```

### Example

```bash
./https_cert_expiry_checker.py example.com sender@email.com -r recipient1@email.com -r recipient2@email.com -t 30
```
