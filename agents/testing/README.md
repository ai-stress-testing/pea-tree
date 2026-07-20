# Testing Team

Empirical verification for the three MVPs and the linear-iterations
queue — the "actually run it" half of the verdict loop
(`agents/WORKFLOW.md`), complementing `logicians/falsifier`'s reasoning
half.

- [`test-automation-engineer/`](test-automation-engineer/) - builds and
  maintains E2E suites (kanban drag-and-drop, queue-turn delivery under a
  killed connection, Mermaid render correctness) and executes any
  falsifier disproof candidate that requires real execution.
