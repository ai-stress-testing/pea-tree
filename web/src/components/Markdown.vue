<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import { marked } from "marked";
import DOMPurify from "dompurify";
import mermaid from "mermaid";

// Live preview pane. Renders markdown, sanitizes the HTML (XSS defense, PRD
// Security), and renders ```mermaid fences as diagrams.
mermaid.initialize({ startOnLoad: false, theme: "dark", securityLevel: "strict" });

const props = defineProps<{ source: string }>();
const html = ref("");
const root = ref<HTMLElement | null>(null);

async function render() {
  const raw = await marked.parse(props.source, { breaks: true });
  html.value = DOMPurify.sanitize(raw);
  // Render mermaid blocks after the sanitized HTML is in the DOM.
  requestAnimationFrame(async () => {
    if (!root.value) return;
    const blocks = root.value.querySelectorAll<HTMLElement>("code.language-mermaid");
    let i = 0;
    for (const block of blocks) {
      try {
        const { svg } = await mermaid.render(`mmd-${Date.now()}-${i++}`, block.textContent ?? "");
        const wrap = document.createElement("div");
        wrap.innerHTML = DOMPurify.sanitize(svg, { USE_PROFILES: { svg: true, svgFilters: true } });
        block.closest("pre")?.replaceWith(wrap);
      } catch {
        /* leave the code block as-is on parse error */
      }
    }
  });
}

onMounted(render);
watch(() => props.source, render);
</script>

<template>
  <!-- eslint-disable-next-line vue/no-v-html -->
  <div ref="root" class="md" v-html="html" />
</template>

<style scoped>
.md { line-height: 1.6; }
.md :deep(pre) { background: #14161a; padding: 12px; border-radius: 8px; overflow-x: auto; }
.md :deep(code) { background: #14161a; padding: 1px 5px; border-radius: 4px; }
.md :deep(table) { border-collapse: collapse; }
.md :deep(td), .md :deep(th) { border: 1px solid #3a3d42; padding: 4px 10px; }
.md :deep(svg) { max-width: 100%; height: auto; }
</style>
