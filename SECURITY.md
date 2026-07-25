# Security policy

AethOS connects to infrastructure and third-party provider accounts, so security
reports are handled privately and with priority.

## Supported versions

Security fixes are made on the latest release and current `main`. Older commits,
forks, and modified deployments are not supported unless a maintainer explicitly
states otherwise.

| Version | Security support |
| --- | --- |
| Latest release | Yes |
| `main` | Best effort until the next release |
| Older releases and snapshots | No |

## Report a vulnerability

Do not open a public issue, discussion, or pull request for a suspected
vulnerability.

Use the repository's **Security → Report a vulnerability** flow to open a private
GitHub Security Advisory. If that feature is unavailable, contact project lead
`@pilotmain` through the contact method on the maintainer's GitHub profile and
share only enough information to establish a private reporting channel.

Include, when available:

- affected version or commit;
- impact and realistic attack scenario;
- minimal reproduction or proof of concept;
- affected configuration or deployment mode;
- suggested mitigation;
- logs or screenshots with tokens, credentials, personal data, and customer data
  removed.

Maintainers aim to acknowledge a complete report within five business days.
Triage, remediation, and disclosure timing depend on severity, exploitability,
affected users, and release complexity. Please allow a reasonable remediation
period before public disclosure.

## Scope

Reports about AethOS source code and project-controlled release artifacts are in
scope. Vulnerabilities solely in an upstream service or dependency should also be
reported to that upstream project; tell us privately if AethOS needs a mitigation.

Research must use accounts and systems you own or have explicit permission to
test. Do not access other users' data, degrade services, persist access, perform
social engineering, or exfiltrate more data than necessary to demonstrate impact.

## Safe harbor

The project will not pursue action against good-faith research that follows this
policy, avoids privacy and availability harm, and gives maintainers a reasonable
opportunity to remediate. This statement does not bind third parties or authorize
testing systems the project does not own.

## Deployment responsibility

AethOS is self-hostable and exposes controls that operators must configure.
Before exposing an instance to a network, review `.env.example`, use least-
privilege provider credentials, enable appropriate authentication, protect the
data directory, terminate TLS, and keep dependencies current. Feature presence is
not a compliance certification. See [docs/ENTERPRISE_SECURITY.md](docs/ENTERPRISE_SECURITY.md)
for implementation guidance and [DISCLAIMER.md](DISCLAIMER.md) for the warranty
terms.
