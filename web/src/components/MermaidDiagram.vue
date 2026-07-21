<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import mermaid from "mermaid";

// Initialize once for the whole app.
let inited = false;
function ensureInit() {
  if (inited) return;
  mermaid.initialize({ startOnLoad: false, theme: "dark", securityLevel: "strict" });
  inited = true;
}

const props = defineProps<{ source: string }>();

const svg = ref("");
const error = ref("");
let seq = 0;
let lastSource = "";

async function render() {
  // Cache by source: an unchanged source is a no-op, not a re-parse.
  if (props.source === lastSource) return;
  lastSource = props.source;
  ensureInit();
  const id = `mmd-${Math.random().toString(36).slice(2)}-${seq++}`;
  try {
    const out = await mermaid.render(id, props.source);
    svg.value = out.svg;
    error.value = "";
  } catch (e) {
    error.value = (e as Error).message;
  }
}

onMounted(render);
watch(() => props.source, render);
</script>

<template>
  <div class="mmd">
    <div v-if="error" class="mmd-error" data-testid="mermaid-error">⚠ {{ error }}</div>
    <!-- eslint-disable-next-line vue/no-v-html -->
    <div v-else class="mmd-canvas" data-testid="mermaid-canvas" v-html="svg" />
  </div>
</template>

<style scoped>
.mmd { width: 100%; }
.mmd-canvas {
  border: 1px solid var(--line); border-radius: 8px; padding: 16px; background: var(--bg-2);
  overflow: auto; display: flex; align-items: center; justify-content: center; min-height: 80px;
}
.mmd-canvas :deep(svg) { max-width: 100%; height: auto; }
.mmd-error {
  border: 1px solid var(--danger); border-radius: 8px; padding: 12px;
  color: var(--danger); font-size: 12px; white-space: pre-wrap; background: rgba(224,92,92,0.06);
}
</style>
