# Issue: Docs — split-editor documentation system (PRIORITY 1)

**Sprint**: sprint-8-26-01-15 · **Source**: `prd.md` §2, §3, §4, §5, §6, §12
**Assignee (parent)**: `frontend/react-dev` (Vue 3 + TS — see C4 note)
**Goal**: Deliver the harness's core value proposition — a
project→sprint→document workspace with a live split-pane markdown editor
and inline AI assistance — so a planner can author and iterate the
document library that the rest of the pipeline consumes.

## Spec

When this issue closes:
- A left sidebar lists projects, each expandable to its sprints; a user
  can create a new sprint from the UI, and within a sprint select any
  document from the fixed library in PRD.md §5 (§5).
- The document view is a split pane with a draggable divider: left =
  markdown editor (syntax highlighting, formatting toolbar), right =
  live preview that updates as the user types (§2).
- Open documents auto-save every 30 s and on blur; no manual save (§3).
- Preview renders standard markdown + Mermaid and sanitizes HTML so no
  injected script executes (§4).
- A user can highlight a passage and either delete it or send it to one
  or more agents selected from a roster data-list with a comment; the
  agent reply returns to the editor (§6).
- Every write goes through TH-0 #3's write-guard and lands only under
  `takt-harness/` (Constraint C1).
- The header shows agent-endpoint availability (§12).

## Sub-issues

### 1. Document CRUD + project/sprint API
- **Assignee**: `backend/backend-dev`
- **Scope**: FastAPI endpoints to list/create projects and sprints,
  list/create/read/update documents (typed by the §5 library), all
  persisted via TH-0's SQLite layer and write-guard.
- **Acceptance criteria**:
  - [ ] Create-project, create-sprint, create/read/update-document
        endpoints exist and persist to SQLite.
  - [ ] New-sprint and document writes hit disk only under `takt-harness/`
        (routes through the write-guard; a write outside is refused).
  - [ ] A document's `type` must be one of the fixed §5 library values;
        an unknown type is rejected.
- **Negative prompt** (do NOT):
  - Do NOT expose any delete endpoint for documents or sprints (PRD
    "No deletions").
  - Do NOT read/write agent files under `ges-talt/` except read-only.
  - Do NOT invent document types beyond the §5 library.
- **Verify**: pytest exercises create→read→update; a write targeting
  `ges-talt/` returns an error and touches no file there.
- **Depends on**: TH-0 #2, #3.

### 2. Draggable split-pane + markdown editor
- **Assignee**: `frontend/react-dev` (Vue 3 + TS)
- **Scope**: The split view — draggable divider adjusting the edit/preview
  ratio, and the left editor (CodeMirror-class, syntax highlighting,
  formatting toolbar with bold/italic/code/table shortcuts).
- **Acceptance criteria**:
  - [ ] Dragging the divider changes the split ratio and the ratio holds
        while typing.
  - [ ] Toolbar buttons and keyboard shortcuts insert correct markdown for
        bold, italic, code block, and table.
  - [ ] Preview keystroke-to-render latency stays under the SRS §5 100 ms
        budget for a 50 KB document.
- **Negative prompt** (do NOT):
  - Do NOT render preview HTML here without the sanitizer from #4 in the
    path.
  - Do NOT implement auto-save here (that is #3) — keep the editor a
    controlled input emitting change events.
  - Do NOT use React; stack is Vue 3 + TS (C4).
- **Verify**: `evidence-collector`/manual — divider drag + toolbar produce
  expected markdown; latency measured.
- **Depends on**: #4 (sanitized render), TH-0 #1.

### 3. Auto-save (30 s + blur)
- **Assignee**: `frontend/react-dev` (Vue 3 + TS)
- **Scope**: Auto-save behavior wiring the editor's change stream to #1's
  update endpoint on a 30 s timer and on blur.
- **Acceptance criteria**:
  - [ ] An edit followed by 30 s idle persists without any click.
  - [ ] Blurring the editor persists immediately.
  - [ ] A failed save surfaces a visible non-blocking error and retries;
        it does not silently drop edits.
- **Negative prompt** (do NOT):
  - Do NOT add a manual "Save" button as the primary persistence path.
  - Do NOT debounce so aggressively that the 30 s guarantee is missed.
  - Do NOT persist by any route other than #1's endpoint.
- **Verify**: manual — edit, wait 30 s, reload shows persisted text; edit,
  blur, reload shows persisted text.
- **Depends on**: #1, #2.

### 4. Markdown + Mermaid render with HTML sanitization (XSS)
- **Assignee**: `security/appsec-engineer`
- **Scope**: The preview render pipeline: standard markdown + Mermaid
  diagram rendering with output HTML sanitized against XSS (§4, SRS §4).
- **Acceptance criteria**:
  - [ ] Standard markdown (headings, lists, code, tables, links) renders.
  - [ ] A fenced `mermaid` block renders as a diagram.
  - [ ] Injected `<script>`, `javascript:` URLs, and `onerror=`/event-
        handler attributes do NOT execute — a sanitization test asserts
        they are stripped/neutralized.
- **Negative prompt** (do NOT):
  - Do NOT allow raw HTML passthrough or `v-html` on unsanitized content.
  - Do NOT disable the sanitizer to make Mermaid work — sanitize around it.
  - Do NOT own the editor UI (that is #2) — this is the render/sanitize
    module only.
- **Verify**: XSS test payloads render inert; Mermaid sample renders.

### 5. Project/sprint sidebar + document-library selection UI
- **Assignee**: `frontend/react-dev` (Vue 3 + TS)
- **Scope**: The left sidebar (projects → expandable sprints), the
  create-sprint control, and the in-sprint document picker over the §5
  library.
- **Acceptance criteria**:
  - [ ] Projects list; expanding one shows its sprints.
  - [ ] "New sprint" creates a sprint via #1 and it appears without reload.
  - [ ] The document picker lists exactly the §5 library entries; picking
        one opens it in the split view.
- **Negative prompt** (do NOT):
  - Do NOT add a delete affordance for projects/sprints/documents.
  - Do NOT hardcode a document list divergent from §5 — source it from #6.
  - Do NOT use React (C4).
- **Verify**: manual — create sprint, open a `prd` doc, confirm persistence.
- **Depends on**: #1, #6.

### 6. Document-library taxonomy definition
- **Assignee**: `design/ux-architect`
- **Scope**: The canonical taxonomy/order/grouping of the §5 document
  library (feature-request … security-review) as a single source both
  frontend (#5) and backend (#1) consume — categories, display order,
  and each type's identifier.
- **Acceptance criteria**:
  - [ ] A definition lists all §5 types, grouped (e.g. Discovery / Design /
        Architecture / Delivery) with stable identifiers.
  - [ ] #1 and #5 reference this definition; no divergent second list.
- **Negative prompt** (do NOT):
  - Do NOT add or remove document types versus PRD.md §5.
  - Do NOT implement UI or storage — taxonomy artifact only.
- **Verify**: definition file exists; #1/#5 identifiers match it 1:1.

### 7. AI-assist: highlight → send-to-agent(s) UI
- **Assignee**: `frontend/react-dev` (Vue 3 + TS)
- **Scope**: Selection UI — highlight a passage, then delete it or open a
  panel to pick one or more agents from a roster data-list, attach a
  comment, submit, and insert/attach the returned reply (§6, SRS §55).
- **Acceptance criteria**:
  - [ ] Highlighting a passage exposes "delete" and "send to agent(s)".
  - [ ] The agent picker is a multi-select data-list of roster roles.
  - [ ] A submitted request shows a pending state and renders the reply
        when it returns; an endpoint error shows a clear error state (§12).
- **Negative prompt** (do NOT):
  - Do NOT call `:1234` directly from the frontend — go through #8's
    backend endpoint.
  - Do NOT auto-apply agent edits silently; the user confirms insertion.
  - Do NOT use React (C4).
- **Verify**: manual — highlight, send to two agents with a comment,
  replies render; delete removes the passage.
- **Depends on**: #8, #2.

### 8. AI-assist backend: agent-review endpoint
- **Assignee**: `ai/ai-engineer`
- **Scope**: A FastAPI endpoint taking (passage, comment, selected agent
  roles), loading each agent's definition from `ges-talt/` read-only,
  calling TH-0 #4's client, and returning per-agent replies.
- **Acceptance criteria**:
  - [ ] Accepts multiple agent roles and returns a reply per role.
  - [ ] Loads agent context from `ges-talt/` read-only (no write there).
  - [ ] Endpoint-unreachable yields a structured "unavailable" per agent,
        not a 500 crash.
- **Negative prompt** (do NOT):
  - Do NOT copy or cache agent files into `takt-harness/` (read in place).
  - Do NOT re-implement retry/backoff — reuse TH-0 #4's client.
  - Do NOT persist agent replies as new documents automatically.
- **Verify**: unit test with stubbed client returns two per-agent replies;
  read-only `ges-talt/` access confirmed.
- **Depends on**: TH-0 #4.

### 9. Adversarial review of Docs
- **Assignee**: `logicians/falsifier`
- **Scope**: Presume Docs violates the invariant or the split-editor/AC5
  claims are false; construct the disproof (a write escaping
  `takt-harness/`, an XSS payload that executes, an autosave that drops
  edits).
- **Acceptance criteria**:
  - [ ] Delivers a concrete counterexample (→ FAIL to the owning sub-issue)
        or an enumerated no-bypass statement across write-path, XSS, and
        autosave-loss vectors.
- **Negative prompt** (do NOT):
  - Do NOT edit code — report only.
  - Do NOT broaden scope to Kanban/Queue/etc.
- **Verify**: report attached; findings reopen the named sub-issue.

## Dependencies

`TH-0 blocks all` · `#6 blocks #1, #5` · `#1 blocks #3, #5` ·
`#4 blocks #2` · `#2 blocks #3, #7` · `#8 blocks #7` · `#9 gates AC5`.
