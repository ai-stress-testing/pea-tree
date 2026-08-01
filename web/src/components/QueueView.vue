<script setup lang="ts">
import { ref, onMounted } from "vue";
import { api, type QueueItem, type AgentTeam } from "../api";

const items = ref<QueueItem[]>([]);
const agents = ref<AgentTeam[]>([]);
const busy = ref<number | null>(null);

async function refresh() { items.value = await api.queue(); }
onMounted(async () => {
  await refresh();
  agents.value = (await api.agents()).teams;
});

const STATE_COLOR: Record<string, string> = {
  idle: "green", processing: "blue", error: "red", done: "done",
  needs_user: "user", paused: "paused",
};

async function process(item: QueueItem) {
  busy.value = item.id;
  try { Object.assign(item, await api.processQueue(item.id)); }
  catch { /* endpoint offline — state already reflects retry */ await refresh(); }
  finally { busy.value = null; }
}
async function pauseResume(item: QueueItem) {
  const state = item.state === "paused" ? "idle" : "paused";
  Object.assign(item, await api.manageQueue(item.id, { state }));
}
async function bump(item: QueueItem, delta: number) {
  Object.assign(item, await api.manageQueue(item.id, { priority: item.priority + delta }));
  await refresh();
}
async function reassign(item: QueueItem, agentId: string) {
  Object.assign(item, await api.manageQueue(item.id, { agent_id: agentId }));
}
</script>

<template>
  <div class="queue">
    <div class="q-head">
      <h2>Agent-Queue</h2>
      <button class="mini" @click="refresh">Refresh</button>
    </div>
    <p v-if="!items.length" class="empty">Queue is empty. Submit an issue in Zettlebucket to enqueue triage.</p>

    <table v-else class="q-table">
      <thead>
        <tr><th>State</th><th>Agent</th><th>Target</th><th>Attempts</th><th>Prio</th><th>Controls</th></tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id">
          <td><span class="state" :class="STATE_COLOR[item.state]">{{ item.state }}</span></td>
          <td>
            <select :value="item.agent_id" @change="reassign(item, ($event.target as HTMLSelectElement).value)">
              <optgroup v-for="t in agents" :key="t.team" :label="t.team">
                <option v-for="a in t.agents" :key="a.id" :value="a.id">{{ a.id }}</option>
              </optgroup>
            </select>
          </td>
          <td>{{ item.target_kind }} #{{ item.target_id }}</td>
          <td>{{ item.attempts }}<span v-if="item.last_error" class="err" :title="item.last_error"> ⚠</span></td>
          <td>
            {{ item.priority }}
            <button class="mini tiny" @click="bump(item, 1)">▲</button>
            <button class="mini tiny" @click="bump(item, -1)">▼</button>
          </td>
          <td class="controls">
            <button class="mini" :disabled="busy === item.id || item.state === 'paused'" @click="process(item)">
              {{ busy === item.id ? "…" : "Process" }}
            </button>
            <button class="mini" @click="pauseResume(item)">{{ item.state === "paused" ? "Resume" : "Pause" }}</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p class="rule">Retry rule: 3 retries → skip; 6 further failures → <span class="state user">needs_user</span>.</p>
  </div>
</template>

<style scoped>
.queue { padding: 20px; overflow: auto; height: 100%; }
.q-head { display: flex; align-items: center; gap: 12px; }
.q-head h2 { margin: 0; }
.empty { color: #9aa0a6; }
.q-table { width: 100%; border-collapse: collapse; margin-top: 12px; }
.q-table th, .q-table td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #3a3d42; font-size: 13px; }
.state { font-size: 11px; padding: 2px 8px; border-radius: 10px; border: 1px solid; }
.state.green { color: #2eb67d; border-color: #2eb67d; }
.state.blue { color: #4a9eff; border-color: #4a9eff; }
.state.red { color: #e05c5c; border-color: #e05c5c; }
.state.user { color: #e0a33e; border-color: #e0a33e; }
.state.done { color: #9aa0a6; border-color: #3a3d42; }
.state.paused { color: #b07be0; border-color: #b07be0; }
.err { color: #e05c5c; cursor: help; }
.controls { display: flex; gap: 6px; }
.mini { font-size: 12px; padding: 3px 8px; border: 1px solid #3a3d42; background: #2b2e33; color: #e8e8e8; border-radius: 5px; cursor: pointer; }
.mini.tiny { padding: 0 4px; }
.rule { color: #9aa0a6; font-size: 12px; margin-top: 16px; }
</style>
