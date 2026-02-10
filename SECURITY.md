# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest release | Yes |
| Previous minor release | Security fixes only |
| Older versions | No |

## Reporting a Vulnerability

We take the security of SelfPublisherForge seriously. If you discover a security vulnerability, please report it responsibly using the process below.

**Do not open a public GitHub issue for security vulnerabilities.**

### How to Report

Send an email to **security@selfpublisherforge.com** with the following information:

- Description of the vulnerability
- Steps to reproduce the issue
- Affected component(s) (e.g., API, frontend, Chrome extension, infrastructure)
- Potential impact and severity assessment
- Any proof-of-concept code or screenshots
- Your name and contact information (for follow-up)

### What to Expect

| Step | Timeline |
|------|----------|
| Acknowledgment of your report | Within 48 hours |
| Initial assessment and severity classification | Within 7 days |
| Status update on remediation | Within 14 days |
| Fix deployed (critical/high severity) | As soon as possible |
| Fix deployed (medium/low severity) | Within next scheduled release |

We will keep you informed throughout the process and credit you in our release notes (unless you prefer to remain anonymous).

## Responsible Disclosure Guidelines

- Allow us reasonable time to investigate and address the vulnerability before making any public disclosure.
- Make a good faith effort to avoid accessing or modifying other users' data.
- Do not exploit the vulnerability beyond what is necessary to demonstrate the issue.
- Do not use automated scanning tools against production systems without prior written authorization.

## Out of Scope

The following are not considered in-scope vulnerabilities:

- Social engineering attacks (e.g., phishing) against employees or users
- Denial of Service (DoS/DDoS) attacks
- Spam or email abuse
- Vulnerabilities in third-party services or dependencies not directly maintained by us
- Issues requiring physical access to a user's device
- Clickjacking on pages with no sensitive actions
- Missing security headers that do not lead to a demonstrable exploit
- Software version disclosure without a demonstrated vulnerability

## Security Practices

SelfPublisherForge implements the following security measures:

- JWT-based authentication with short-lived access tokens and refresh token rotation
- Multi-factor authentication (MFA) support
- Role-based access control (RBAC) with row-level data isolation
- Rate limiting on all API endpoints
- Input validation and parameterized database queries
- Automated dependency auditing via `pip-audit` and `npm audit` in CI
- Infrastructure managed via Terraform with least-privilege IAM policies
- Secrets stored in AWS SSM Parameter Store (never in source code)

## Contact

For security-related inquiries: **security@selfpublisherforge.com**

For licensing inquiries: **licensing@selfpublisherforge.com**
