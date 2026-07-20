# Backend Team

Owns the shared data model, API contracts, and realtime transport behind
the three MVPs (kanban, messaging, Mermaid) and the linear-iterations
queue that runs on top of them.

- [`backend-architect/`](backend-architect/) - schema, API contracts, and
  ADRs for the backend as a whole; advisory (Write-only, no Edit/Bash).
- [`realtime-collaboration-engineer/`](realtime-collaboration-engineer/) -
  implements the WebSocket/SSE transport that delivers messaging-MVP
  turns in strict, resumable order.

Full-stack UI implementation (including wiring to this team's contracts)
is `frontend/react-dev`'s job, not this team's — see that team's README
for the split.
