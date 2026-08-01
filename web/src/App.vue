<script setup lang="ts">
import { ref, onMounted } from "vue";
import { api, type AgentStatus } from "./api";
import DocsView from "./components/DocsView.vue";

type View = "docs" | "kanban" | "queue" | "zettel" | "chats";
const view = ref<View>("docs");
const status = ref<AgentStatus | null>(null);

const nav: { id: View; label: string; ready: boolean }[] = [
  { id: "docs", label: "Docs", ready: true },
  { id: "kanban", label: "Kanban", ready: false },
  { id: "queue", label: "Agent-Queue", ready: false },
  { id: "zettel", label: "Zettlebucket", ready: false },
  { id: "chats", label: "Chats", ready: false },
];

onMounted(async () => {
  try { status.value = await api.agentStatus(); } catch { status.value = null; }
});
</script>

<template>
  <div class="shell">
    <nav class="nav">
      <h1>Takt-Harness <span class="sub">30B planning harness</span></h1>
      <button
        v-for="n in nav"
        :key="n.id"
        class="nav-item"
        :class="{ active: view === n.id }"
        @click="view = n.id"
      >
        {{ n.label }}
        <span v-if="!n.ready" class="soon">soon</span>
      </button>
      <div class="spacer" />
      <div class="agent-badge">
        <span class="dot" :class="{ ok: status?.available, bad: status && !status.available }" />
        <span v-if="!status">agent: checking…</span>
        <span v-else-if="status.available">agent online ({{ status.models.length }} model)</span>
        <span v-else>agent offline · :1234</span>
      </div>
    </nav>

    <main class="main">
      <DocsView v-if="view === 'docs'" />
      <div v-else class="stub">
        <h2>{{ nav.find((n) => n.id === view)?.label }}</h2>
        <p>Specced in <code>docs/issue-specs/</code>; Docs (priority 1) ships first per the PRD.</p>
      </div>
    </main>
  </div>
</template>

<style scoped>
.shell { display: grid; grid-template-columns: 200px 1fr; height: 100vh; }
.nav { background: #15171a; border-right: 1px solid #3a3d42; display: flex; flex-direction: column; padding: 12px 8px; gap: 3px; }
.nav h1 { font-size: 14px; margin: 4px 10px 12px; }
.sub { display: block; font-size: 10px; color: #9aa0a6; font-weight: 400; }
.nav-item { display: flex; justify-content: space-between; align-items: center; text-align: left; background: transparent; border: none; color: #9aa0a6; padding: 8px 10px; border-radius: 6px; cursor: pointer; }
.nav-item:hover { background: #2b2e33; color: #e8e8e8; }
.nav-item.active { background: #2b2e33; color: #e8e8e8; font-weight: 600; }
.soon { font-size: 9px; color: #6b7075; border: 1px solid #3a3d42; border-radius: 8px; padding: 0 5px; }
.spacer { flex: 1; }
.agent-badge { display: flex; align-items: center; gap: 6px; font-size: 11px; color: #9aa0a6; padding: 8px 10px; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: #9aa0a6; }
.dot.ok { background: #2eb67d; } .dot.bad { background: #e05c5c; }
.main { min-width: 0; overflow: hidden; }
.stub { padding: 32px; color: #9aa0a6; }
</style>
