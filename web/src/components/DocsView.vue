<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from "vue";
import { api, type Project, type DocMeta, type Doc, type LibraryItem } from "../api";
import Markdown from "./Markdown.vue";

const projects = ref<Project[]>([]);
const library = ref<LibraryItem[]>([]);
const expanded = ref<Record<number, boolean>>({});
const activeSprint = ref<number | null>(null);
const sprintDocs = ref<DocMeta[]>([]);
const doc = ref<Doc | null>(null);
const editor = ref("");
const saved = ref(true);
const chosenType = ref("");

// split ratio (edit pane width fraction)
const ratio = ref(0.5);
const dragging = ref(false);

onMounted(async () => {
  projects.value = await api.projects();
  library.value = await api.library();
});

async function newProject() {
  const name = prompt("Project name?");
  if (!name) return;
  projects.value.push(await api.createProject(name));
}
async function newSprint(projectId: number) {
  const name = prompt("Sprint name?");
  if (!name) return;
  const s = await api.createSprint(projectId, name);
  const p = projects.value.find((x) => x.id === projectId);
  p?.sprints.push(s);
  expanded.value[projectId] = true;
}
function toggle(projectId: number) {
  expanded.value[projectId] = !expanded.value[projectId];
}
async function openSprint(sprintId: number) {
  activeSprint.value = sprintId;
  sprintDocs.value = await api.documents(sprintId);
  doc.value = null;
}
async function addDoc() {
  if (!activeSprint.value || !chosenType.value) return;
  const d = await api.createDocument(activeSprint.value, chosenType.value);
  sprintDocs.value.push({ id: d.id, doc_type: d.doc_type, title: d.title });
  chosenType.value = "";
  await openDoc(d.id);
}
async function openDoc(id: number) {
  doc.value = await api.document(id);
  editor.value = doc.value.content;
  saved.value = true;
}

watch(editor, () => { saved.value = false; });

async function save() {
  if (!doc.value || saved.value) return;
  const updated = await api.saveDocument(doc.value.id, editor.value);
  doc.value.updated_at = updated.updated_at;
  saved.value = true;
}

// Auto-save: every 30s and on blur (PRD Docs design note).
let timer: number | undefined;
onMounted(() => { timer = window.setInterval(save, 30_000); });
onBeforeUnmount(() => window.clearInterval(timer));

// Draggable divider.
function startDrag() { dragging.value = true; }
function onMove(e: MouseEvent) {
  if (!dragging.value) return;
  const el = document.getElementById("split");
  if (!el) return;
  const r = el.getBoundingClientRect();
  ratio.value = Math.min(0.85, Math.max(0.15, (e.clientX - r.left) / r.width));
}
function endDrag() { dragging.value = false; }
onMounted(() => {
  window.addEventListener("mousemove", onMove);
  window.addEventListener("mouseup", endDrag);
});
onBeforeUnmount(() => {
  window.removeEventListener("mousemove", onMove);
  window.removeEventListener("mouseup", endDrag);
});

// AI-assist on a highlighted selection (SRS §3.5).
const assistOpen = ref(false);
const selection = ref("");
const instruction = ref("");
const assistResults = ref<{ agent: string; text?: string; error?: string }[]>([]);
function openAssist() {
  const sel = window.getSelection()?.toString() ?? "";
  selection.value = sel || editor.value.slice(0, 400);
  assistOpen.value = true;
  assistResults.value = [];
}
async function runAssist() {
  if (!doc.value) return;
  const res = await api.agentAssist(doc.value.id, selection.value, instruction.value, []);
  assistResults.value = res.results;
}

const editWidth = computed(() => `${ratio.value * 100}%`);
</script>

<template>
  <div class="docs">
    <aside class="sidebar">
      <div class="side-head">
        Projects <button class="mini" @click="newProject">+ Project</button>
      </div>
      <div v-for="p in projects" :key="p.id" class="proj">
        <div class="proj-row" @click="toggle(p.id)">
          <span>{{ expanded[p.id] ? "▾" : "▸" }} {{ p.name }}</span>
          <button class="mini" @click.stop="newSprint(p.id)">+ Sprint</button>
        </div>
        <div v-if="expanded[p.id]" class="sprints">
          <button
            v-for="s in p.sprints"
            :key="s.id"
            class="sprint-row"
            :class="{ active: activeSprint === s.id }"
            @click="openSprint(s.id)"
          >{{ s.name }}</button>
        </div>
      </div>

      <template v-if="activeSprint">
        <div class="side-head">Documents</div>
        <button
          v-for="d in sprintDocs"
          :key="d.id"
          class="doc-row"
          :class="{ active: doc?.id === d.id }"
          @click="openDoc(d.id)"
        >{{ d.title }} <span class="tag">{{ d.doc_type }}</span></button>
        <div class="add-doc">
          <select v-model="chosenType">
            <option value="">+ Add document…</option>
            <option v-for="l in library" :key="l.type" :value="l.type">{{ l.label }}</option>
          </select>
          <button class="mini" :disabled="!chosenType" @click="addDoc">Add</button>
        </div>
      </template>
    </aside>

    <section v-if="doc" id="split" class="split">
      <div class="pane edit" :style="{ width: editWidth }">
        <div class="pane-bar">
          <input v-model="doc.title" class="title-input" @blur="save" />
          <span class="save-state">{{ saved ? "saved" : "editing…" }}</span>
          <button class="mini" @click="openAssist">Ask agents</button>
        </div>
        <textarea v-model="editor" class="src" spellcheck="false" @blur="save" />
      </div>
      <div class="divider" @mousedown="startDrag" />
      <div class="pane preview">
        <div class="pane-bar">Preview</div>
        <div class="preview-body"><Markdown :source="editor" /></div>
      </div>
    </section>
    <section v-else class="empty">
      <p>Select a sprint and open a document, or add one from the library.</p>
    </section>

    <div v-if="assistOpen" class="assist-overlay" @click.self="assistOpen = false">
      <div class="assist">
        <h3>Ask agents about the selection</h3>
        <textarea v-model="selection" class="assist-sel" rows="4" />
        <input v-model="instruction" placeholder="Correction or consideration…" />
        <div class="assist-actions">
          <button class="mini" @click="assistOpen = false">Close</button>
          <button class="mini primary" @click="runAssist">Send</button>
        </div>
        <div v-for="r in assistResults" :key="r.agent" class="assist-result">
          <strong>{{ r.agent }}</strong>
          <div>{{ r.text || r.error }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.docs { display: grid; grid-template-columns: 240px 1fr; height: 100%; min-height: 0; }
.sidebar { border-right: 1px solid #3a3d42; overflow-y: auto; padding: 10px; }
.side-head { display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; font-size: 11px; color: #9aa0a6; margin: 12px 4px 6px; }
.proj-row { display: flex; justify-content: space-between; align-items: center; padding: 4px; cursor: pointer; border-radius: 6px; }
.proj-row:hover { background: #2b2e33; }
.sprints { padding-left: 12px; }
.sprint-row, .doc-row { display: block; width: 100%; text-align: left; background: transparent; border: none; color: #e8e8e8; padding: 5px 6px; border-radius: 6px; cursor: pointer; }
.sprint-row:hover, .doc-row:hover { background: #2b2e33; }
.sprint-row.active, .doc-row.active { background: #2b2e33; color: #4a9eff; }
.tag { color: #9aa0a6; font-size: 10px; }
.add-doc { display: flex; gap: 6px; margin-top: 8px; }
.add-doc select { flex: 1; }
.split { display: flex; min-width: 0; }
.pane { display: flex; flex-direction: column; min-width: 0; }
.pane.preview { flex: 1; }
.pane-bar { display: flex; gap: 8px; align-items: center; padding: 8px 12px; border-bottom: 1px solid #3a3d42; font-size: 12px; color: #9aa0a6; }
.title-input { flex: 1; background: transparent; border: none; color: #e8e8e8; font-size: 14px; font-weight: 600; }
.save-state { font-size: 11px; }
.src { flex: 1; background: #14161a; color: #e8e8e8; border: none; resize: none; padding: 14px; font-family: ui-monospace, monospace; font-size: 13px; line-height: 1.6; }
.divider { width: 6px; cursor: col-resize; background: #3a3d42; }
.divider:hover { background: #4a9eff; }
.preview-body { flex: 1; overflow-y: auto; padding: 14px; }
.empty { display: flex; align-items: center; justify-content: center; color: #9aa0a6; }
.mini { font-size: 12px; padding: 3px 8px; border: 1px solid #3a3d42; background: #2b2e33; color: #e8e8e8; border-radius: 5px; cursor: pointer; }
.mini.primary { background: #4a9eff; color: #06203d; border-color: #4a9eff; }
.assist-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; }
.assist { background: #222529; border: 1px solid #3a3d42; border-radius: 10px; padding: 18px; width: 560px; max-height: 80vh; overflow-y: auto; }
.assist h3 { margin: 0 0 10px; }
.assist textarea, .assist input { width: 100%; margin-bottom: 8px; background: #14161a; color: #e8e8e8; border: 1px solid #3a3d42; border-radius: 6px; padding: 8px; }
.assist-actions { display: flex; justify-content: flex-end; gap: 8px; }
.assist-result { margin-top: 12px; padding: 10px; background: #14161a; border-radius: 8px; }
</style>
