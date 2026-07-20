# Frontend Team

Owns UI/UX intent and implementation for the three MVPs: the kanban board
(issue #2), the messaging/queue-chat view (issue #3), and the Mermaid
render pane (issue #4).

- [`designer/`](designer/) - design spec (layout, states, accessibility)
  for each surface; read/write docs only, never production code.
- [`react-dev/`](react-dev/) - implements the spec in React, wired to the
  backend contracts from `backend/backend-architect`.

Split: `designer` decides what the UI should be and how it should behave;
`react-dev` builds it and verifies it in a running browser. Ambiguous
design intent routes designer→PM, never guessed at by react-dev.
