# Logicians Team

Static review and adversarial rigor, at opus, read-only by design — the
model spend buys reasoning depth, never a wider blast radius (no
Edit/Bash/Write on this team, no exceptions).

- [`software-architect/`](software-architect/) - cross-MVP architecture:
  how the queue, board, chat, and diagram renderer compose as one system.
- [`falsifier/`](falsifier/) - the harness's adversary grader
  (`agents/WORKFLOW.md`'s verdict loop): presumes an artifact is wrong and
  tries to construct the disproof before it ships.

Both roles are read-only Read/Grep/Glob; empirical re-execution of a
falsifier candidate is `testing/test-automation-engineer`'s job, not this
team's.
