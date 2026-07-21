# Issue: Iterative groupchat pipeline (priority #1)

**Sprint**: sprint-7-26-20-27 · **Source**: `prd.md` §4, §5
**Assignee (parent)**: `agents/ai/multi-agent-systems-architect`
**Goal**: the harness's core loop — a user posts one message; the system
decides *who is involved* from the roster, then iteratively prompts each
involved persona (fresh context, seeded with the goal + prior turns) until
the queue is exhausted, and synthesizes a final result. This is the
"fake groupchat" of issue #1/#5, built on Vue + TS + Ollama.

## Spec

The pipeline is: **`message → select participants → ordered iterate →
(re-queue?) → synthesize final`**.

1. **Select participants.** Given the user message and the roster manifest
   (role id + one-line description), produce the involved subset and their
   order. Two inputs merge: explicit `@team/role` mentions in the message
   (always included) and an LLM router call over the roster (fills in the
   rest). Proximity ordering from `agents/ORCHESTRATION.md` applies:
   security and legal near the front of consultation, logicians last.
2. **Iterate.** For each queue position, build a prompt = persona charter
   + initial goal + prior turns (a compact running transcript, not the
   full raw history), call Ollama in a **fresh context**, and append the
   turn. Each turn records `role`, `cycle`, and `tokenCost`
   (`prompt_eval_count + eval_count` from Ollama).
3. **Re-queue.** `security/senior-secops` (Opsec) and
   `legal/product-counsel` (legal) may emit a structured
   `REQUEUE: <team/role>` directive; the engine re-inserts that role after
   the current position **iff** the run is under its re-queue cap
   (default 2). Past the cap, the directive is recorded but not acted on —
   the queue always terminates.
4. **Synthesize.** A final call (reason tier) folds the goal + every turn
   into the final result (the plan). Cumulative token cost and cycle count
   are reported.
5. **Model interchange.** Persona `model:` tiers (opus/sonnet/haiku ⇒
   reason/build/cheap) resolve through a settings-level tier→Ollama-model
   map validated against `GET /api/tags`; no concrete model id is baked in.

## Sub-issues

### 1. Pipeline topology + contracts (design)
- **Assignee**: `agents/ai/multi-agent-systems-architect`
- **Scope**: the queue's ordering rule, the per-turn prompt contract, the
  re-queue directive grammar + cap, and the termination argument.
- **Acceptance criteria**:
  - [ ] The participant-selection contract (mentions ∪ router output,
        proximity-ordered) is written down, including the router's JSON
        output shape.
  - [ ] Re-queue grammar (`REQUEUE: <team/role>`) and cap are specified,
        with a stated proof that the queue terminates.
  - [ ] Per-cycle token-growth target (~500–1000) is defined as a reported
        metric with an overflow rule.
- **Negative prompt** (do NOT): implement the Vue/TS engine here; choose
  concrete Ollama model ids (that is a runtime setting, not a design fact).
- **Verify**: design doc reviewed by `agents/logicians/software-architect`.

### 2. Ollama client (interchangeable model)
- **Assignee**: `agents/backend/realtime-collaboration-engineer`
- **Scope**: a typed TS client for `POST /api/chat` (streaming NDJSON) and
  `GET /api/tags`, plus the tier→model resolver.
- **Acceptance criteria**:
  - [ ] `chat()` streams tokens and returns `{text, promptTokens,
        evalTokens}` on completion.
  - [ ] Model is a parameter, never a constant; the resolver maps a tier
        to a model present in `/api/tags`, falling back to the first
        available model with a visible warning if the configured one is
        absent.
  - [ ] A killed/aborted stream rejects cleanly without leaking the reader.
- **Negative prompt** (do NOT): call any non-Ollama endpoint; hard-code a
  model id anywhere outside the default settings object.
- **Verify**: `agents/testing/test-automation-engineer` covers a streamed
  completion and an aborted stream against a mock `fetch`.

### 3. Groupchat engine (iterate + re-queue)
- **Assignee**: `agents/ai/prompt-engineer`
- **Scope**: the `runGroupchat()` engine — participant selection, the
  fresh-context iteration loop, re-queue handling, and final synthesis —
  wired to the persona manifest generated from `agents/`.
- **Acceptance criteria**:
  - [ ] Each turn is prompted with a fresh context of (charter + goal +
        prior-turn digest), never the raw full transcript.
  - [ ] A run with at least one re-queue still terminates within the cap.
  - [ ] Every turn carries `role`, `cycle`, `tokenCost`; the run reports
        cumulative tokens and cycle count.
  - [ ] Personas come from the generated roster manifest, so adding a role
        in `agents/` makes it selectable with no engine edit.
- **Negative prompt** (do NOT): let a persona self-report its own credited
  token number (`agents/COMMS.md` — the engine records it); embed prompt
  text for a persona inline instead of loading its charter.
- **Verify**: engine unit test drives a scripted 4-persona run with one
  re-queue and asserts termination + accounting.

### 4. Slack-like messaging UI
- **Assignee**: `agents/frontend/react-dev` (Vue implementer)
- **Scope**: the messaging view — a channel/thread layout, an @-mention
  composer, and a live turn stream rendering each persona's turn with its
  role/cycle/token badge as it arrives.
- **Acceptance criteria**:
  - [ ] Posting a message starts a run and streams turns into the thread
        in order, each labeled with role, cycle, and token cost.
  - [ ] A re-queue turn is visually distinct from a first-pass turn.
  - [ ] The final synthesized result is pinned at the end of the thread.
  - [ ] Loading/empty/error/streaming states are all rendered.
- **Negative prompt** (do NOT): build the Mermaid or kanban views here;
  block the UI thread while streaming.
- **Verify**: `agents/pm/project-manager` acceptance against this spec;
  runs in a browser against a live Ollama.

## Dependencies

- #1 blocks #3 (contract before engine).
- #2 blocks #3 (client before the engine that calls it).
- #3 blocks #4 (engine before the UI that drives it).
