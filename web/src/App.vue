<script setup lang="ts">
import { store, actions, View } from "./store";
import Messaging from "./components/Messaging.vue";
import MermaidView from "./components/MermaidView.vue";
import KanbanView from "./components/KanbanView.vue";
import SettingsPanel from "./components/SettingsPanel.vue";

const items: { view: View; label: string; icon: string }[] = [
  { view: "messaging", label: "Messaging", icon: "#" },
  { view: "mermaid", label: "Mermaid", icon: "◇" },
  { view: "kanban", label: "Kanban", icon: "▦" },
  { view: "settings", label: "Settings", icon: "⚙" },
];
</script>

<template>
  <div class="app-shell">
    <nav class="nav">
      <h1>pea-tree <span class="brand-sub">groupchat harness · Ollama</span></h1>
      <button
        v-for="it in items"
        :key="it.view"
        class="nav-item"
        :class="{ active: store.view === it.view }"
        @click="actions.setView(it.view)"
      >
        <span style="display:inline-block;width:16px;color:var(--muted)">{{ it.icon }}</span>
        {{ it.label }}
      </button>
      <div class="nav-spacer" />
      <div class="ollama-badge">
        <span
          class="dot"
          :class="{ ok: store.ollamaOk === true, bad: store.ollamaOk === false }"
        />
        <span v-if="store.ollamaOk === null">checking Ollama…</span>
        <span v-else-if="store.ollamaOk">Ollama · {{ store.models.length }} model(s)</span>
        <span v-else>Ollama offline</span>
      </div>
    </nav>

    <Messaging v-if="store.view === 'messaging'" />
    <MermaidView v-else-if="store.view === 'mermaid'" />
    <KanbanView v-else-if="store.view === 'kanban'" />
    <SettingsPanel v-else-if="store.view === 'settings'" />
  </div>
</template>
