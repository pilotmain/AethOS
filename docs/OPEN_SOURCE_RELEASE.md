# Open-source release controls

The repository contains the files needed for an Apache-2.0 open-source project.
Some protections are repository-host settings and must be enabled on GitHub by an
administrator; they cannot be enforced by files in a clone.

## Before changing repository visibility

- Confirm the copyright notice in `NOTICE` and `COPYRIGHT.md` matches the legal
  ownership records for the original work.
- Confirm every included third-party asset and copied source file has compatible
  licensing and any required attribution.
- Review the complete Git history for credentials and sensitive data. Scanning
  only the current tree is not sufficient if the repository will expose history.
- Verify that private vulnerability and conduct reporting can reach a maintainer.
- Remove or redact real customer, employee, infrastructure, production, and
  incident data from every branch and tag intended for publication.

## GitHub repository settings

Create a ruleset for `main` that:

- requires pull requests and at least one approving review;
- requires review from code owners;
- dismisses stale approvals when new commits are pushed;
- requires all review conversations to be resolved;
- requires the CI, Security, and DCO status checks;
- blocks force-pushes and branch deletion;
- restricts bypass permissions to emergency maintainers.

Also enable private vulnerability reporting, Dependabot alerts and security
updates, secret scanning, and push protection where the GitHub plan supports
them. Protect release environments and credentials separately from pull-request
workflows.

## First public release

1. Run the tests and public-release audit in CI.
2. Review dependency audit and SBOM artifacts.
3. Update [CHANGELOG.md](../CHANGELOG.md) and the package version.
4. Create a signed or otherwise verified version tag.
5. Publish release notes with upgrade steps, known limitations, and security
   fixes.
6. Re-run the public repository's community-profile and security settings audit.
