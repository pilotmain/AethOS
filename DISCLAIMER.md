# AethOS — Disclaimer & Responsible-Use Notice

AethOS is a **governed AI operations platform**: it can inspect systems, draft
changes, and — only after explicit human approval — execute actions against the
infrastructure and accounts you connect. Read this before relying on it.

## No warranty

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE, AND NON-INFRINGEMENT. The copyright holder is not liable for any
claim, damages, or other liability arising from the use of the software, to the
maximum extent permitted by law.

## You own the actions you approve

- AethOS is **approval-gated**: consequential actions (deployments, mutations,
  sending messages, posting, etc.) require your explicit approval. **You are
  responsible for what you approve.** Review the blast radius, rollback plan, and
  risk tier before approving.
- AethOS runs on **your own provider keys and accounts**, billed to you. You are
  responsible for those credentials, the costs they incur, and compliance with each
  provider's terms.

## AI output is not guaranteed correct

Model output (including the multi-model arbiter's consensus) can be wrong, biased,
or incomplete. Treat it as **assistive**, not authoritative. Do not use AethOS as the
sole basis for legal, financial, medical, safety, or other high-stakes decisions.
Verify before acting.

## Data & isolation

Each tenant's workspace is isolated and credentials are stored in an encrypted vault.
Connecting a third-party service (a model provider, a social platform, a repo host)
sends data to that service under its own terms and privacy policy. You are
responsible for what you connect and what you share.

## Security

Do not use AethOS to take actions you are not authorized to take. Secure your
account, rotate keys you suspect are exposed, and revoke access you no longer need.
