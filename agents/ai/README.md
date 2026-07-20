# AI Team

Owns the models, prompts, and agent pipeline that give pea-tree its core
feature: the "linear iterations" harness (issue #5) — a queue of personas
a low-intelligence, large-context planning model steps through before an
expensive model ever writes code.

- [`multi-agent-systems-architect/`](multi-agent-systems-architect/) -
  designs the queue's topology, per-cycle token budget, and re-queue rule.
- [`prompt-engineer/`](prompt-engineer/) - turns each queue position's
  contract into a tested, versioned prompt for the target model tier.

Same `agent.md` + `SPEC.md` convention as every other team in this repo.
Add a role here when it owns a durable subclass of AI/pipeline work — not
per MVP.
