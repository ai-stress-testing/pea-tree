<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { store, actions } from "../store";
import type { Card } from "../store";

// New-card composer state, keyed per column.
const draftTitle = ref<Record<string, string>>({});
const draftRef = ref<Record<string, string>>({});
const editingId = ref<string | null>(null);
const editTitle = ref("");
const editRef = ref("");

onMounted(() => {
  if (!store.boardLoaded) actions.loadBoard();
});

const lastColOrder = computed(() =>
  store.columns.reduce((m, c) => Math.max(m, c.order), 0),
);

function add(columnId: string) {
  const title = draftTitle.value[columnId] ?? "";
  if (!title.trim()) return;
  actions.addCard(columnId, title, draftRef.value[columnId] ?? "");
  draftTitle.value[columnId] = "";
  draftRef.value[columnId] = "";
}

function startEdit(card: Card) {
  editingId.value = card.id;
  editTitle.value = card.title;
  editRef.value = card.issueRef;
}
function saveEdit(card: Card) {
  actions.editCard(card.id, { title: editTitle.value, issueRef: editRef.value });
  editingId.value = null;
}

// Native drag-and-drop (enhancement); button/keyboard moves are the
// deterministic path the tests drive.
const dragId = ref<string | null>(null);
function onDrop(columnId: string) {
  if (dragId.value) actions.moveCard(dragId.value, columnId);
  dragId.value = null;
}
</script>

<template>
  <div class="pane">
    <div class="pane-header">
      <strong>Kanban</strong>
      <span v-if="store.board" class="badge">{{ store.board.name }}</span>
      <div style="flex:1" />
      <span class="badge">{{ store.cards.length }} card(s)</span>
    </div>

    <div v-if="!store.boardLoaded" class="pane-body"><p class="stub">Loading board…</p></div>

    <div v-else class="board" data-testid="board">
      <section
        v-for="col in store.columns"
        :key="col.id"
        class="column"
        :data-testid="`column-${col.id}`"
        @dragover.prevent
        @drop="onDrop(col.id)"
      >
        <header class="col-head">
          <div class="col-title">
            {{ col.name }}
            <span
              class="badge count"
              :class="{ over: actions.overWip(col.id) }"
              :data-testid="`count-${col.id}`"
            >
              {{ actions.cardsIn(col.id).length }}<template v-if="col.wipLimit != null">/{{ col.wipLimit }}</template>
            </span>
          </div>
          <div class="rules" :title="`entry: ${col.entryRule}\nexit: ${col.exitRule}`">
            ↳ {{ col.entryRule }}
          </div>
        </header>

        <div class="cards">
          <article
            v-for="card in actions.cardsIn(col.id)"
            :key="card.id"
            class="card"
            :data-testid="`card-${card.id}`"
            draggable="true"
            @dragstart="dragId = card.id"
          >
            <template v-if="editingId === card.id">
              <input v-model="editTitle" class="edit-title" data-testid="edit-title" />
              <input v-model="editRef" class="edit-ref" placeholder="issue ref" />
              <div class="card-actions">
                <button class="mini" data-testid="save-edit" @click="saveEdit(card)">Save</button>
                <button class="mini" @click="editingId = null">Cancel</button>
              </div>
            </template>
            <template v-else>
              <div class="card-title">{{ card.title }}</div>
              <div class="card-foot">
                <span v-if="card.issueRef" class="badge ref">{{ card.issueRef }}</span>
                <div style="flex:1" />
                <button
                  class="mini nav"
                  :disabled="col.order === 0"
                  :aria-label="`move ${card.title} left`"
                  :data-testid="`left-${card.id}`"
                  @click="actions.moveCardDir(card.id, -1)"
                >◀</button>
                <button
                  class="mini nav"
                  :disabled="col.order === lastColOrder"
                  :aria-label="`move ${card.title} right`"
                  :data-testid="`right-${card.id}`"
                  @click="actions.moveCardDir(card.id, 1)"
                >▶</button>
                <button class="mini" :data-testid="`edit-${card.id}`" @click="startEdit(card)">✎</button>
                <button class="mini" :data-testid="`del-${card.id}`" @click="actions.deleteCard(card.id)">✕</button>
              </div>
            </template>
          </article>

          <p v-if="actions.cardsIn(col.id).length === 0" class="col-empty">No cards.</p>
        </div>

        <div class="composer">
          <input
            v-model="draftTitle[col.id]"
            class="add-title"
            :data-testid="`add-title-${col.id}`"
            placeholder="+ Add a card"
            @keydown.enter="add(col.id)"
          />
          <input
            v-model="draftRef[col.id]"
            class="add-ref"
            :data-testid="`add-ref-${col.id}`"
            placeholder="issue ref (e.g. #7)"
            @keydown.enter="add(col.id)"
          />
          <button class="mini" :data-testid="`add-${col.id}`" @click="add(col.id)">Add</button>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.board {
  flex: 1; overflow-x: auto; display: flex; gap: 14px; padding: 18px; align-items: flex-start;
}
.column {
  flex: 0 0 280px; background: var(--bg-2); border: 1px solid var(--line);
  border-radius: 10px; display: flex; flex-direction: column; max-height: 100%;
}
.col-head { padding: 12px 12px 8px; border-bottom: 1px solid var(--line); }
.col-title { display: flex; align-items: center; gap: 8px; font-weight: 600; }
.count.over { color: var(--danger); border-color: var(--danger); }
.rules { color: var(--muted); font-size: 11px; margin-top: 4px; }
.cards { padding: 10px; display: flex; flex-direction: column; gap: 8px; overflow-y: auto; flex: 1; }
.col-empty { color: var(--muted); font-size: 12px; margin: 4px 2px; }
.card {
  background: var(--bg-3); border: 1px solid var(--line); border-radius: 8px; padding: 10px;
}
.card-title { line-height: 1.4; margin-bottom: 8px; }
.card-foot, .card-actions { display: flex; align-items: center; gap: 4px; }
.ref { color: var(--accent); }
.mini { padding: 2px 7px; font-size: 12px; border-radius: 5px; }
.mini.nav { min-width: 26px; }
.composer { padding: 10px; border-top: 1px solid var(--line); display: flex; flex-direction: column; gap: 6px; }
.add-title, .add-ref, .edit-title, .edit-ref { width: 100%; }
</style>
