# Security Team

Owns defensive controls and the Opsec seat in the linear-iterations queue
(issue #5) — consulted before a design ships, with standing authority to
re-queue the goal to an earlier position if it finds a risk.

- [`senior-secops/`](senior-secops/) - scans for secrets/sensitive-data
  exposure first, then audits/implements standard controls (authN/Z,
  headers, CORS, rate limiting, CSP) across the kanban, messaging, and
  Mermaid surfaces.

Per `agents/ORCHESTRATION.md`'s consultation-proximity ordering, security
is pulled in close to the orchestrator — early, not as an afterthought.
