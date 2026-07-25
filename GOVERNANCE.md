# Project governance

AethOS uses maintainer-led, transparent governance. Technical discussion happens
in public issues and pull requests except when confidentiality is required for a
security or conduct report.

## Roles

- **Contributors** propose issues, documentation, tests, and code through pull
  requests.
- **Reviewers** are trusted contributors who provide domain review but do not
  merge unless they also hold maintainer permissions.
- **Maintainers** triage, review, merge, release, moderate, and protect project
  infrastructure.
- **Project lead:** Raya Meresa (`@pilotmain`) is the initial maintainer and final
  decision maker when consensus cannot be reached.

Maintainer status is earned through sustained, constructive contributions,
sound judgment, security awareness, and reliable review. The project lead may
appoint or remove maintainers after documenting the decision. Inactive
maintainers may be moved to emeritus status.

## Decisions

Routine decisions are made through pull-request review. Significant changes
should start with an issue describing motivation, alternatives, compatibility,
security impact, and migration. Maintainers seek rough consensus; the project
lead resolves deadlocks and may reject changes that weaken safety, maintainability,
licensing clarity, or project scope.

Security incidents may be handled privately until coordinated disclosure is
safe. Urgent fixes can use an expedited review, but still require a second-person
review when another maintainer is available and must receive retrospective
documentation.

## Protected decisions

Changes to the license, copyright statements, contribution terms, code of
conduct, governance model, release credentials, or security policy require the
project lead's approval. Such a change cannot remove rights already granted or
relicense third-party contributions without appropriate permission.

## Releases

Maintainers publish versioned releases from protected `main` after required
checks pass. Release notes identify behavior changes, security fixes, migrations,
and known limitations. See [CONTRIBUTING.md](CONTRIBUTING.md) for merge controls.
