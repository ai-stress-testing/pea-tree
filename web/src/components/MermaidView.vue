<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { store, actions } from "../store";
import MermaidDiagram from "./MermaidDiagram.vue";

onMounted(() => {
  if (!store.diagrams.length) actions.loadDiagrams();
});

const active = computed(() => actions.activeDiagram());

// Local editable copy of the source, synced to the store (debounced persist).
const source = ref(active.value?.source ?? "");
const name = ref(active.value?.name ?? "");
watch(active, (d) => {
  source.value = d?.source ?? "";
  name.value = d?.name ?? "";
});

let timer: number | undefined;
function onSource() {
  if (!active.value) return;
  clearTimeout(timer);
  const id = active.value.id;
  const val = source.value;
  timer = window.setTimeout(() => actions.updateDiagram(id, { source: val }), 250);
}
function onName() {
  if (active.value) actions.updateDiagram(active.value.id, { name: name.value });
}
</script>

<template>
  <div class="pane">
    <div class="pane-header">
      <strong>Mermaid</strong>
      <span class="badge">live render · saved</span>
      <div style="flex:1" />
      <button data-testid="new-diagram" @click="actions.addDiagram()">+ New</button>
    </div>

    <div class="mermaid-layout">
      <aside class="diagram-list">
        <button
          v-for="d in store.diagrams"
          :key="d.id"
          class="diagram-row"
          :class="{ active: d.id === store.activeDiagramId }"
          :data-testid="`diagram-${d.id}`"
          @click="actions.selectDiagram(d.id)"
        >
          <span class="d-name">{{ d.name }}</span>
          <span
            class="d-del"
            role="button"
            :data-testid="`del-diagram-${d.id}`"
            title="delete"
            @click.stop="actions.deleteDiagram(d.id)"
          >✕</span>
        </button>
        <p v-if="!store.diagrams.length" class="empty">No diagrams. Click + New.</p>
      </aside>

      <div v-if="active" class="editor-area">
        <input
          v-model="name"
          class="d-title"
          data-testid="diagram-name"
          placeholder="Diagram name"
          @input="onName"
        />
        <div class="split">
          <textarea
            v-model="source"
            class="src"
            data-testid="diagram-source"
            spellcheck="false"
            @input="onSource"
          />
          <div class="preview">
            <MermaidDiagram :source="source" />
          </div>
        </div>
      </div>
      <div v-else class="editor-area">
        <p class="empty">Select or create a diagram.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mermaid-layout { flex: 1; display: grid; grid-template-columns: 200px 1fr; min-height: 0; }
.diagram-list { border-right: 1px solid var(--line); overflow-y: auto; padding: 10px 8px; }
.diagram-row {
  display: flex; align-items: center; justify-content: space-between; gap: 6px;
  width: 100%; text-align: left; border: none; background: transparent;
  border-radius: 6px; padding: 8px; margin-bottom: 2px;
}
.diagram-row:hover { background: var(--bg-3); }
.diagram-row.active { background: var(--bg-3); }
.d-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.d-del { color: var(--muted); font-size: 12px; padding: 0 4px; }
.d-del:hover { color: var(--danger); }
.empty { color: var(--muted); font-size: 12px; padding: 8px; }
.editor-area { display: flex; flex-direction: column; min-height: 0; padding: 16px; gap: 12px; }
.d-title { font-size: 15px; font-weight: 600; }
.split { flex: 1; display: grid; grid-template-columns: 1fr 1fr; gap: 16px; min-height: 0; }
.src { font-family: ui-monospace, monospace; font-size: 13px; resize: none; min-height: 320px; }
.preview { overflow: auto; }
</style>
