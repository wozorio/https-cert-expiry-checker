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

1. Set an environment variable with the SendGrid API key:

   ```bash
   export SENDGRID_API_KEY=<SENDGRID_API_KEY>
   ```

1. Install [uv](https://docs.astral.sh/uv/):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

### Usage

```bash
Usage: https_cert_expiry_checker.py URL SENDER [OPTIONS]

Arguments:
  URL         The domain to check for certificate expiration date (e.g., example.com)
  SENDER      The email address used as the sender for emails
  RECIPIENTS  A comma-separated list of recipients to send emails to


Options:
  --version                Show the version and exit.
  -t, --threshold INTEGER  days before expiry to notify (default: 60)
  --help                   Show this message and exit.
```

### Example

```bash
./https_cert_expiry_checker.py example.com sender@email.com -r recipient1@email.com -r recipient2@email.com -t 30
```
