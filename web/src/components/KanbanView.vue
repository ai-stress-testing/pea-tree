<script setup lang="ts">
// Kanban is the next interface after the groupchat (prd.md priority order).
// Stubbed intentionally so effort stays on the priority-1 pipeline; the
// board/column/card model is specced in docs/.../issue-specs/kanban-mvp.md.
</script>

<template>
  <div class="pane">
    <div class="pane-header">
      <strong>Kanban</strong>
      <span class="badge">next up</span>
    </div>
    <div class="pane-body">
      <div class="stub">
        <h3>Kanban board — not built yet</h3>
        <p>
          The board where a converged plan's tickets land. Per the sprint PRD,
          the iterative groupchat ships first; this view follows.
        </p>
        <p>
          Spec: <code>docs/sprint-7-26-20-27/issue-specs/kanban-mvp.md</code>
          (board/column/card model, explicit column entry/exit rules, issue-ID
          traceability). Owner: <code>frontend/react-dev</code> with
          <code>pm/ticket-workflow-steward</code> on the column state machine.
        </p>
      </div>
    </div>
  </div>
</template>
