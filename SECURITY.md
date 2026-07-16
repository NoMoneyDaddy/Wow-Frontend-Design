# Security policy

## Supported versions

Security fixes target the current `main` branch and latest tagged release. Older snapshots are not maintained; reproduce against a current revision before reporting when possible.

## Report a vulnerability

Do not place credentials, personal data, exploit payloads, or other sensitive details in a public issue. GitHub private vulnerability reporting is not currently enabled for this repository. Until a confidential channel is enabled, open a minimal issue titled `Private security contact requested` with only the affected area and a way for a maintainer to contact you; do not include the vulnerability details there.

Non-sensitive dependency, documentation, or hardening findings may use a normal issue.

When a private channel is established, include:

- the affected release or full commit;
- the impacted Skill, script, evaluator, or generated-output boundary;
- environment and exact reproduction steps using test data only;
- expected impact and any known prerequisite;
- the smallest safe proof of concept;
- suggested mitigation, if known.

Never send real API keys, tokens, passwords, customer data, or third-party content without permission. Report upstream dependency vulnerabilities to the upstream project as well when appropriate.

## Disclosure

Allow maintainers time to reproduce, fix, and publish an advisory before public disclosure. This volunteer project does not promise a response SLA; status and disclosure timing should be agreed through the private channel.
