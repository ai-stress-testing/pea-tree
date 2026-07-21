<script setup lang="ts">
import { ref, computed, nextTick, watch } from "vue";
import { store, actions } from "../store";
import TurnCard from "./TurnCard.vue";

const draft = ref("");
const bodyEl = ref<HTMLElement | null>(null);

const thread = computed(() => actions.activeThread());
const running = computed(() => {
  const t = thread.value;
  return !!t && (t.status === "running" || t.status === "synth");
});

function send() {
  const text = draft.value.trim();
  if (!text || store.ollamaOk === false) return;
  actions.startRun(text);
  draft.value = "";
}

function onKey(e: KeyboardEvent) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
}

// Auto-scroll the conversation as turns stream in.
watch(
  () => [thread.value?.turns.length, thread.value?.final, thread.value?.status],
  async () => {
    await nextTick();
    bodyEl.value?.scrollTo({ top: bodyEl.value.scrollHeight, behavior: "smooth" });
  },
  { deep: true },
);

function statusLabel(s: string): string {
  return { running: "iterating", synth: "synthesizing", done: "done", error: "error" }[s] ?? s;
}
</script>

<template>
  <div class="pane messaging">
    <div class="thread-list">
      <div class="thread-list-head">Runs</div>
      <p v-if="!store.threads.length" class="empty-hint">
        No runs yet. Post a goal to start a groupchat.
      </p>
      <button
        v-for="t in store.threads"
        :key="t.id"
        class="thread-row"
        :class="{ active: t.id === store.activeThreadId }"
        @click="actions.select(t.id)"
      >
        <div class="thread-goal">{{ t.goal }}</div>
        <div class="thread-meta">
          <span class="badge">{{ statusLabel(t.status) }}</span>
          <span v-if="t.totals">{{ t.totals.tokens }} tok · {{ t.totals.cycles }} cyc</span>
          <span v-else>{{ t.turns.length }} turn(s)</span>
        </div>
      </button>
    </div>

    <div class="conversation">
      <div class="pane-header">
        <span class="hash">#</span>
        <strong>groupchat</strong>
        <span v-if="thread" class="badge">{{ statusLabel(thread.status) }}</span>
        <div style="flex:1" />
        <span v-if="thread?.totals" class="badge tok">
          {{ thread.totals.tokens }} tok · {{ thread.totals.cycles }} cycles ·
          {{ thread.totals.requeues }} re-queue(s)
        </span>
        <button v-if="running && thread" @click="actions.cancel(thread.id)">Stop</button>
      </div>

      <div ref="bodyEl" class="pane-body conv-body">
        <div v-if="!thread" class="stub">
          <h3>Iterative groupchat</h3>
          <p>
            Post a goal below. The harness picks which roster personas are involved,
            prompts each one in turn (fresh context, seeded with the goal + prior
            turns), lets <code>security/senior-secops</code> and
            <code>legal/product-counsel</code> re-queue an earlier agent, then
            synthesizes a final plan.
          </p>
          <p>Force participants with <code>@team/role</code> mentions, e.g.
            <code>@frontend/designer</code>.</p>
        </div>

        <template v-else>
          <div v-if="thread.participants.length" class="participants">
            <span class="participants-label">involved:</span>
            <span v-for="id in thread.participants" :key="id" class="chip">{{ id }}</span>
          </div>

          <div class="goal-msg">
            <div class="avatar you">YOU</div>
            <div class="turn-body">
              <div class="turn-head"><span class="turn-name">you</span></div>
              <div class="turn-text">{{ thread.goal }}</div>
            </div>
          </div>

          <TurnCard v-for="t in thread.turns" :key="t.id" :turn="t" />

          <div v-for="(n, i) in thread.notices" :key="i" class="notice">⚠ {{ n }}</div>

          <div v-if="thread.final || thread.finalStreaming" class="final">
            <div class="final-head">
              ★ Final plan
              <span v-if="thread.finalStreaming" class="badge streaming">▍ synthesizing</span>
            </div>
            <div class="turn-text">{{ thread.final || "…" }}</div>
          </div>
        </template>
      </div>

      <div class="composer">
        <textarea
          v-model="draft"
          rows="2"
          :disabled="store.ollamaOk === false"
          placeholder="Message the groupchat — describe an MVP goal. @team/role to force a participant. Enter to send."
          @keydown="onKey"
        />
        <button class="primary" :disabled="!draft.trim() || store.ollamaOk === false" @click="send">
          Send
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.messaging { display: grid; grid-template-columns: 240px 1fr; }
.thread-list { border-right: 1px solid var(--line); overflow-y: auto; padding: 10px 8px; }
.thread-list-head {
  text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;
  color: var(--muted); padding: 4px 8px 10px;
}
.empty-hint { color: var(--muted); font-size: 12px; padding: 0 8px; line-height: 1.5; }
.thread-row {
  display: block; width: 100%; text-align: left; border: none; background: transparent;
  border-radius: 6px; padding: 8px; margin-bottom: 2px;
}
.thread-row:hover { background: var(--bg-3); }
.thread-row.active { background: var(--bg-3); }
.thread-goal {
  font-size: 13px; margin-bottom: 4px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.thread-meta { display: flex; gap: 6px; align-items: center; font-size: 11px; color: var(--muted); }

.conversation { display: flex; flex-direction: column; min-width: 0; }
.conv-body { display: flex; flex-direction: column; gap: 2px; }

.participants { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin-bottom: 10px; }
.participants-label { color: var(--muted); font-size: 12px; }
.chip { font-size: 11px; padding: 2px 8px; border-radius: 10px; background: var(--bg-3); color: var(--accent); }

.goal-msg { display: flex; gap: 12px; padding: 10px 4px; }
.avatar {
  width: 36px; height: 36px; flex-shrink: 0; border-radius: 8px; background: var(--bg-3);
  display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 11px;
}
.avatar.you { color: var(--accent-2); }
.turn-body { flex: 1; min-width: 0; }
.turn-head { display: flex; gap: 8px; margin-bottom: 3px; }
.turn-name { font-weight: 600; }
.turn-text { white-space: pre-wrap; line-height: 1.55; word-break: break-word; }

.notice { color: var(--warn); font-size: 12px; padding: 4px 8px; }

.final {
  margin: 14px 0 6px; padding: 14px; border: 1px solid var(--accent-2);
  border-radius: 10px; background: rgba(46, 182, 125, 0.06);
}
.final-head { font-weight: 700; color: var(--accent-2); margin-bottom: 8px; display: flex; gap: 8px; align-items: center; }
.tok { color: var(--accent-2); }
.streaming { color: var(--accent); }

.composer { display: flex; gap: 8px; padding: 12px 18px; border-top: 1px solid var(--line); }
.composer textarea { flex: 1; resize: none; }
</style>
