<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from "vue";
import { api, type Project, type DocMeta, type Doc, type LibraryItem } from "../api";
import Markdown from "./Markdown.vue";
import { exportMarkdown, exportPdf } from "../lib/export";

const projects = ref<Project[]>([]);
const library = ref<LibraryItem[]>([]);
const expanded = ref<Record<number, boolean>>({});
const activeSprint = ref<number | null>(null);
const sprintDocs = ref<DocMeta[]>([]);
const doc = ref<Doc | null>(null);
const editor = ref("");
const title = ref("");
const saved = ref(true);
const titleError = ref("");
const chosenType = ref("");
const renamingId = ref<number | null>(null);

const ratio = ref(0.5);
const dragging = ref(false);
const editorEl = ref<HTMLTextAreaElement | null>(null);
const previewEl = ref<HTMLElement | null>(null);
const exportOpen = ref(false);

onMounted(async () => {
  projects.value = await api.projects();
  library.value = await api.library();
});

// ---- F2: category-grouped library + sprint documents ----
const categories = computed(() => {
  const order: string[] = [];
  for (const l of library.value) if (!order.includes(l.category)) order.push(l.category);
  return order;
});
function libInCategory(cat: string): LibraryItem[] {
  return library.value.filter((l) => l.category === cat);
}
const catOf: Record<string, string> = {};
watch(library, () => { for (const l of library.value) catOf[l.type] = l.category; });
function docsByCategory(): { category: string; docs: DocMeta[] }[] {
  const groups: Record<string, DocMeta[]> = {};
  for (const d of sprintDocs.value) (groups[catOf[d.doc_type] ?? "Other"] ??= []).push(d);
  return Object.entries(groups).map(([category, docs]) => ({ category, docs }));
}

async function newProject() {
  const name = prompt("Project name?");
  if (!name) return;
  projects.value.push(await api.createProject(name));
}
async function newSprint(projectId: number) {
  const name = prompt("Sprint name?");
  if (!name) return;
  const s = await api.createSprint(projectId, name);
  projects.value.find((x) => x.id === projectId)?.sprints.push(s);
  expanded.value[projectId] = true;
}
function toggle(projectId: number) { expanded.value[projectId] = !expanded.value[projectId]; }

async function openSprint(sprintId: number) {
  activeSprint.value = sprintId;
  sprintDocs.value = await api.documents(sprintId);
  doc.value = null;
}
async function addDoc() {
  if (!activeSprint.value || !chosenType.value) return;
  try {
    const d = await api.createDocument(activeSprint.value, chosenType.value);
    sprintDocs.value.push({ id: d.id, doc_type: d.doc_type, title: d.title });
    chosenType.value = "";
    await openDoc(d.id);
  } catch (e) {
    alert(errMessage(e));
  }
}
async function openDoc(id: number) {
  doc.value = await api.document(id);
  editor.value = doc.value.content;
  title.value = doc.value.title;
  saved.value = true;
  titleError.value = "";
  assistOpen.value = false;
  // F4: reset scroll to top on document switch.
  await nextTick();
  editorEl.value?.scrollTo({ top: 0 });
  previewEl.value?.scrollTo({ top: 0 });
}

watch(editor, () => { saved.value = false; });

function errMessage(e: unknown): string {
  const m = (e as Error).message ?? "";
  try {
    const body = JSON.parse(m.slice(m.indexOf("{")));
    const d = body.detail ?? body;
    return d.message ? `${d.message}${d.suggestion ? ` Try: "${d.suggestion}".` : ""}` : m;
  } catch { return m; }
}

async function save() {
  if (!doc.value || (saved.value && title.value === doc.value.title)) return;
  try {
    const updated = await api.saveDocument(doc.value.id, editor.value, title.value);
    doc.value.title = updated.title;
    doc.value.updated_at = updated.updated_at;
    const meta = sprintDocs.value.find((d) => d.id === doc.value!.id);
    if (meta) meta.title = updated.title;
    saved.value = true;
    titleError.value = "";
  } catch (e) {
    titleError.value = errMessage(e);
    title.value = doc.value.title; // revert to the persisted title
  }
}

// F2: inline rename from the sidebar.
function startRename(d: DocMeta) { renamingId.value = d.id; }
async function commitRename(d: DocMeta, newTitle: string) {
  renamingId.value = null;
  if (!newTitle.trim() || newTitle === d.title) return;
  try {
    const cur = doc.value?.id === d.id ? editor.value : (await api.document(d.id)).content;
    const updated = await api.saveDocument(d.id, cur, newTitle);
    d.title = updated.title;
    if (doc.value?.id === d.id) { doc.value.title = updated.title; title.value = updated.title; }
  } catch (e) { alert(errMessage(e)); }
}

// Auto-save (30s + blur).
let timer: number | undefined;
onMounted(() => { timer = window.setInterval(save, 30_000); });
onBeforeUnmount(() => window.clearInterval(timer));

// ---- F5: export ----
function doExportMd() { if (doc.value) exportMarkdown(title.value, editor.value); exportOpen.value = false; }
function doExportPdf() {
  const html = previewEl.value?.querySelector(".md")?.innerHTML ?? "";
  exportPdf(title.value, html);
  exportOpen.value = false;
}

// ---- draggable divider ----
function startDrag() { dragging.value = true; }
function onMove(e: MouseEvent) {
  if (!dragging.value) return;
  const el = document.getElementById("split");
  if (!el) return;
  const r = el.getBoundingClientRect();
  ratio.value = Math.min(0.85, Math.max(0.15, (e.clientX - r.left) / r.width));
}
function endDrag() { dragging.value = false; }
onMounted(() => { window.addEventListener("mousemove", onMove); window.addEventListener("mouseup", endDrag); });
onBeforeUnmount(() => { window.removeEventListener("mousemove", onMove); window.removeEventListener("mouseup", endDrag); });

// ---- F3: inline (selection) vs full-document ask ----
const assistOpen = ref(false);
const assistScope = ref<"selection" | "document">("selection");
const selection = ref("");
const instruction = ref("");
const assistResults = ref<{ agent: string; text?: string; error?: string }[]>([]);
const assistBusy = ref(false);
const floater = ref<{ x: number; y: number } | null>(null);

function currentSelection(): string {
  const el = editorEl.value;
  if (!el) return "";
  return el.value.slice(el.selectionStart, el.selectionEnd);
}
function onEditorMouseUp(e: MouseEvent) {
  const sel = currentSelection();
  floater.value = sel.trim() ? { x: e.clientX, y: e.clientY } : null;
}
function openInlineAsk() {
  const sel = currentSelection();
  if (!sel.trim()) return;
  assistScope.value = "selection";
  selection.value = sel;
  floater.value = null;
  assistOpen.value = true;
  assistResults.value = [];
}
function openFullDocAsk() {
  assistScope.value = "document";
  selection.value = editor.value;
  assistOpen.value = true;
  assistResults.value = [];
}
async function runAssist() {
  if (!doc.value) return;
  assistBusy.value = true;
  try {
    const res = await api.agentAssist(doc.value.id, selection.value, instruction.value, []);
    assistResults.value = res.results;
  } catch (e) {
    assistResults.value = [{ agent: "—", error: errMessage(e) }];
  } finally {
    assistBusy.value = false;
  }
}
function onKey(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openInlineAsk(); }
}

const editWidth = computed(() => `${ratio.value * 100}%`);
</script>

<template>
  <div class="docs" @keydown="onKey">
    <aside class="sidebar">
      <div class="side-head">Projects <button class="mini" @click="newProject">+ Project</button></div>
      <div v-for="p in projects" :key="p.id" class="proj">
        <div class="proj-row" @click="toggle(p.id)">
          <span>{{ expanded[p.id] ? "▾" : "▸" }} {{ p.name }}</span>
          <button class="mini" @click.stop="newSprint(p.id)">+ Sprint</button>
        </div>
        <div v-if="expanded[p.id]" class="sprints">
          <button v-for="s in p.sprints" :key="s.id" class="sprint-row"
                  :class="{ active: activeSprint === s.id }" @click="openSprint(s.id)">{{ s.name }}</button>
        </div>
      </div>

      <template v-if="activeSprint">
        <div class="side-head">Documents</div>
        <!-- F2: created documents grouped by category -->
        <div v-for="g in docsByCategory()" :key="g.category" class="cat-group">
          <div class="cat-label">{{ g.category }}</div>
          <div v-for="d in g.docs" :key="d.id" class="doc-row-wrap">
            <input v-if="renamingId === d.id" class="rename" :value="d.title" autofocus
                   @keydown.enter="commitRename(d, ($event.target as HTMLInputElement).value)"
                   @blur="commitRename(d, ($event.target as HTMLInputElement).value)" />
            <button v-else class="doc-row" :class="{ active: doc?.id === d.id }" @click="openDoc(d.id)"
                    @dblclick="startRename(d)" :title="'Double-click to rename'">
              {{ d.title }} <span class="tag">{{ d.doc_type }}</span>
            </button>
          </div>
        </div>
        <!-- F2: category-grouped add-document picker -->
        <div class="add-doc">
          <select v-model="chosenType">
            <option value="">+ Add document…</option>
            <optgroup v-for="cat in categories" :key="cat" :label="cat">
              <option v-for="l in libInCategory(cat)" :key="l.type" :value="l.type">{{ l.label }}</option>
            </optgroup>
          </select>
          <button class="mini" :disabled="!chosenType" @click="addDoc">Add</button>
        </div>
      </template>
    </aside>

    <section v-if="doc" id="split" class="split">
      <div class="pane edit" :style="{ width: editWidth }">
        <div class="pane-bar">
          <input v-model="title" class="title-input" @blur="save" />
          <span class="save-state" :class="{ err: titleError }">{{ titleError || (saved ? "saved" : "editing…") }}</span>
          <div class="bar-actions">
            <div class="export">
              <button class="mini" @click="exportOpen = !exportOpen">Export ▾</button>
              <div v-if="exportOpen" class="export-menu">
                <button @click="doExportMd">Save as Markdown (.md)</button>
                <button @click="doExportPdf">Save as PDF</button>
              </div>
            </div>
            <button class="mini" data-testid="full-doc-ask" @click="openFullDocAsk">Analyze Full Document</button>
          </div>
        </div>
        <textarea ref="editorEl" v-model="editor" class="src" spellcheck="false"
                  @blur="save" @mouseup="onEditorMouseUp" />

        <!-- F3: collapsible agent-response panel (does not replace content) -->
        <div v-if="assistOpen" class="assist-panel">
          <div class="assist-head">
            {{ assistScope === "document" ? "Full-document analysis" : "Ask agent about selection" }}
            <button class="mini" @click="assistOpen = false">✕</button>
          </div>
          <div class="assist-sel">{{ selection.slice(0, 240) }}<span v-if="selection.length > 240">…</span></div>
          <div class="assist-run">
            <input v-model="instruction" placeholder="Instruction (rewrite / summarize / check tone…)" />
            <button class="mini primary" :disabled="assistBusy" @click="runAssist">{{ assistBusy ? "…" : "Send" }}</button>
          </div>
          <div v-for="r in assistResults" :key="r.agent" class="assist-result">
            <strong>{{ r.agent }}</strong><div>{{ r.text || r.error }}</div>
          </div>
        </div>
      </div>

      <div class="divider" @mousedown="startDrag" />
      <div class="pane preview">
        <div class="pane-bar">Preview</div>
        <div ref="previewEl" class="preview-body"><Markdown :source="editor" /></div>
      </div>
    </section>
    <section v-else class="empty"><p>Select a sprint and open a document, or add one from the library.</p></section>

    <!-- F3: floating inline ask button near the selection -->
    <button v-if="floater" class="floater" :style="{ left: floater.x + 'px', top: floater.y + 8 + 'px' }"
            data-testid="inline-ask" @mousedown.prevent="openInlineAsk">Ask Agent ⌘K</button>
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
.cat-group { margin-bottom: 6px; }
.cat-label { font-size: 10px; text-transform: uppercase; color: #6b7075; margin: 6px 6px 2px; letter-spacing: 0.4px; }
.rename { width: 100%; }
.tag { color: #9aa0a6; font-size: 10px; }
.add-doc { display: flex; gap: 6px; margin-top: 10px; }
.add-doc select { flex: 1; }
.split { display: flex; min-width: 0; }
.pane { display: flex; flex-direction: column; min-width: 0; min-height: 0; }
.pane.preview { flex: 1; }
.pane-bar { display: flex; gap: 8px; align-items: center; padding: 8px 12px; border-bottom: 1px solid #3a3d42; font-size: 12px; color: #9aa0a6; }
.title-input { flex: 1; background: transparent; border: none; color: #e8e8e8; font-size: 14px; font-weight: 600; }
.save-state { font-size: 11px; white-space: nowrap; }
.save-state.err { color: #e05c5c; max-width: 260px; overflow: hidden; text-overflow: ellipsis; }
.bar-actions { display: flex; gap: 6px; }
.export { position: relative; }
.export-menu { position: absolute; right: 0; top: 26px; background: #222529; border: 1px solid #3a3d42; border-radius: 8px; z-index: 5; display: flex; flex-direction: column; min-width: 190px; }
.export-menu button { text-align: left; background: transparent; border: none; color: #e8e8e8; padding: 8px 12px; cursor: pointer; }
.export-menu button:hover { background: #2b2e33; }
/* F4: independent scroll + generous bottom padding, smooth. */
.src { flex: 1; overflow: auto; scroll-behavior: smooth; background: #14161a; color: #e8e8e8; border: none; resize: none; padding: 14px 14px 48px; font-family: ui-monospace, monospace; font-size: 13px; line-height: 1.6; }
.divider { width: 6px; cursor: col-resize; background: #3a3d42; }
.divider:hover { background: #4a9eff; }
.preview-body { flex: 1; overflow: auto; scroll-behavior: smooth; padding: 14px 14px 48px; }
.empty { display: flex; align-items: center; justify-content: center; color: #9aa0a6; }
.mini { font-size: 12px; padding: 3px 8px; border: 1px solid #3a3d42; background: #2b2e33; color: #e8e8e8; border-radius: 5px; cursor: pointer; }
.mini.primary { background: #4a9eff; color: #06203d; border-color: #4a9eff; }
.assist-panel { border-top: 1px solid #3a3d42; background: #1c1f24; padding: 10px 12px; max-height: 40%; overflow-y: auto; }
.assist-head { display: flex; justify-content: space-between; font-weight: 600; color: #4a9eff; margin-bottom: 6px; }
.assist-sel { font-size: 12px; color: #9aa0a6; border-left: 2px solid #3a3d42; padding-left: 8px; margin-bottom: 8px; white-space: pre-wrap; }
.assist-run { display: flex; gap: 8px; margin-bottom: 8px; }
.assist-run input { flex: 1; }
.assist-result { background: #14161a; border-radius: 8px; padding: 10px; margin-top: 8px; white-space: pre-wrap; }
.floater { position: fixed; z-index: 20; background: #4a9eff; color: #06203d; border: none; border-radius: 6px; padding: 5px 10px; font-size: 12px; font-weight: 600; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.4); }
</style>
