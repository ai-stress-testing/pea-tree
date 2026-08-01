<script setup lang="ts">
import { ref, onMounted } from "vue";
import { api, type ZettelTemplate } from "../api";

const templates = ref<ZettelTemplate[]>([]);
const title = ref("");
const description = ref("");
const priority = ref("medium");
const tags = ref("");
const flash = ref("");

onMounted(async () => { templates.value = await api.zettelTemplates(); });

function applyTemplate(t: ZettelTemplate) {
  description.value = t.description;
  priority.value = t.priority;
  if (!title.value) title.value = t.label + ": ";
}

async function submit() {
  if (!title.value.trim()) return;
  const issue = await api.zettelSubmit({
    title: title.value, description: description.value, priority: priority.value, tags: tags.value,
  });
  flash.value = `Submitted #${issue.id} → routed to Agent-Queue for triage.`;
  title.value = ""; description.value = ""; tags.value = ""; priority.value = "medium";
  setTimeout(() => (flash.value = ""), 4000);
}

// Ctrl+Enter submits (PRD keyboard shortcut).
function onKey(e: KeyboardEvent) {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) submit();
}
</script>

<template>
  <div class="zettel" @keydown="onKey">
    <h2>Zettlebucket</h2>
    <p class="sub">Fast intake. A submitted issue lands in the Kanban Zettlebucket column and routes to the Agent-Queue.</p>

    <div class="templates">
      <button v-for="t in templates" :key="t.id" class="tmpl" @click="applyTemplate(t)">{{ t.label }}</button>
    </div>

    <input v-model="title" class="title" placeholder="Issue title" />
    <textarea v-model="description" class="desc" rows="8" placeholder="Description (markdown)" />
    <div class="row">
      <select v-model="priority">
        <option value="low">low</option><option value="medium">medium</option><option value="high">high</option>
      </select>
      <input v-model="tags" class="tags" placeholder="tags, comma, separated" />
      <button class="submit" @click="submit">Submit <kbd>⌘↵</kbd></button>
    </div>
    <p v-if="flash" class="flash">{{ flash }}</p>
  </div>
</template>

<style scoped>
.zettel { padding: 24px; max-width: 720px; }
.zettel h2 { margin: 0 0 4px; }
.sub { color: #9aa0a6; margin-top: 0; }
.templates { display: flex; gap: 8px; margin: 14px 0; }
.tmpl { padding: 6px 12px; border: 1px solid #3a3d42; background: #2b2e33; color: #e8e8e8; border-radius: 16px; cursor: pointer; }
.tmpl:hover { border-color: #4a9eff; }
.title { width: 100%; margin-bottom: 10px; font-size: 15px; }
.desc { width: 100%; font-family: ui-monospace, monospace; font-size: 13px; margin-bottom: 10px; }
.row { display: flex; gap: 10px; align-items: center; }
.tags { flex: 1; }
.submit { padding: 8px 16px; background: #4a9eff; color: #06203d; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; }
kbd { background: rgba(0,0,0,0.2); border-radius: 3px; padding: 0 4px; font-size: 11px; }
.flash { color: #2eb67d; margin-top: 12px; }
</style>
