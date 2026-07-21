<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import mermaid from "mermaid";

mermaid.initialize({ startOnLoad: false, theme: "dark", securityLevel: "strict" });

const source = ref(`flowchart LR
  U[User message] --> R{Who is involved?}
  R -->|mentions ∪ router| Q[Ordered queue]
  Q --> T1[PM] --> T2[Architect] --> T3[Front-end]
  T3 --> Op[Opsec] --> Lg[Legal]
  Op -. re-queue .-> T2
  Lg --> F[[Final plan]]`);

const svg = ref("");
const error = ref("");
let seq = 0;

async function render() {
  const id = `mmd-${seq++}`;
  try {
    const out = await mermaid.render(id, source.value);
    svg.value = out.svg;
    error.value = "";
  } catch (e) {
    error.value = (e as Error).message;
  }
}

onMounted(render);
let timer: number | undefined;
watch(source, () => {
  clearTimeout(timer);
  timer = window.setTimeout(render, 300);
});
</script>

<template>
  <div class="pane">
    <div class="pane-header">
      <strong>Mermaid</strong>
      <span class="badge">live render</span>
    </div>
    <div class="pane-body mermaid-grid">
      <div class="editor">
        <label class="hint">Diagram source</label>
        <textarea v-model="source" spellcheck="false" />
        <p v-if="error" class="err">⚠ {{ error }}</p>
      </div>
      <div class="preview">
        <label class="hint">Preview</label>
        <!-- eslint-disable-next-line vue/no-v-html -->
        <div class="canvas" v-html="svg" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.mermaid-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
.editor, .preview { display: flex; flex-direction: column; gap: 6px; min-height: 0; }
textarea { flex: 1; min-height: 340px; resize: vertical; font-family: ui-monospace, monospace; font-size: 13px; }
.canvas {
  flex: 1; border: 1px solid var(--line); border-radius: 8px; padding: 16px;
  background: var(--bg-2); overflow: auto; display: flex; align-items: center; justify-content: center;
}
.canvas :deep(svg) { max-width: 100%; height: auto; }
.err { color: var(--danger); font-size: 12px; white-space: pre-wrap; }
.hint { color: var(--muted); font-size: 12px; }
</style>
