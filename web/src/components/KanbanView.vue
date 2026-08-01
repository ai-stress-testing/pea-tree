<script setup lang="ts">
import { ref, onMounted } from "vue";
import { api, type Stage, type Issue, type Project } from "../api";

const stages = ref<Stage[]>([]);
const issues = ref<Issue[]>([]);
const projects = ref<Project[]>([]);
const newTitle = ref("");
const newPriority = ref("medium");

onMounted(async () => {
  [stages.value, issues.value, projects.value] = await Promise.all([
    api.stages(), api.issues(), api.projects(),
  ]);
});

function inStage(stageId: string): Issue[] {
  return issues.value.filter((i) => i.stage === stageId);
}
function stageIndex(stageId: string): number {
  return stages.value.findIndex((s) => s.id === stageId);
}

async function addIssue() {
  if (!newTitle.value.trim()) return;
  issues.value.push(await api.createIssue(newTitle.value, newPriority.value));
  newTitle.value = "";
}
async function move(issue: Issue, dir: -1 | 1) {
  const idx = stageIndex(issue.stage) + dir;
  const target = stages.value[idx];
  if (!target) return;
  const updated = await api.updateIssue(issue.id, { stage: target.id });
  Object.assign(issue, updated);
}
async function assign(issue: Issue, projectId: number | null) {
  const updated = await api.updateIssue(issue.id, { project_id: projectId });
  Object.assign(issue, updated);
}

const dragId = ref<number | null>(null);
async function onDrop(stageId: string) {
  const issue = issues.value.find((i) => i.id === dragId.value);
  if (issue && issue.stage !== stageId) {
    const updated = await api.updateIssue(issue.id, { stage: stageId });
    Object.assign(issue, updated);
  }
  dragId.value = null;
}
</script>

<template>
  <div class="board">
    <section
      v-for="(s, si) in stages"
      :key="s.id"
      class="col"
      @dragover.prevent
      @drop="onDrop(s.id)"
    >
      <header class="col-head">
        {{ s.label }} <span class="count">{{ inStage(s.id).length }}</span>
      </header>

      <div class="cards">
        <article
          v-for="issue in inStage(s.id)"
          :key="issue.id"
          class="card"
          draggable="true"
          @dragstart="dragId = issue.id"
        >
          <div class="card-title">{{ issue.title }}</div>
          <div class="card-meta">
            <span class="pri" :class="issue.priority">{{ issue.priority }}</span>
            <select
              class="assign"
              :value="issue.project_id ?? ''"
              @change="assign(issue, ($event.target as HTMLSelectElement).value ? Number(($event.target as HTMLSelectElement).value) : null)"
            >
              <option value="">unassigned</option>
              <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </div>
          <div class="card-nav">
            <button class="mini" :disabled="si === 0" @click="move(issue, -1)">◀</button>
            <button class="mini" :disabled="si === stages.length - 1" @click="move(issue, 1)">▶</button>
          </div>
        </article>
      </div>

      <div v-if="si === 0" class="intake">
        <input v-model="newTitle" placeholder="+ Quick issue" @keydown.enter="addIssue" />
        <select v-model="newPriority">
          <option value="low">low</option>
          <option value="medium">medium</option>
          <option value="high">high</option>
        </select>
        <button class="mini" @click="addIssue">Add</button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.board { display: flex; gap: 12px; padding: 16px; height: 100%; overflow-x: auto; align-items: flex-start; }
.col { flex: 0 0 260px; background: #222529; border: 1px solid #3a3d42; border-radius: 10px; display: flex; flex-direction: column; max-height: 100%; }
.col-head { padding: 10px 12px; border-bottom: 1px solid #3a3d42; font-weight: 600; display: flex; justify-content: space-between; }
.count { color: #9aa0a6; font-weight: 400; }
.cards { padding: 10px; display: flex; flex-direction: column; gap: 8px; overflow-y: auto; flex: 1; }
.card { background: #2b2e33; border: 1px solid #3a3d42; border-radius: 8px; padding: 10px; }
.card-title { margin-bottom: 8px; line-height: 1.4; }
.card-meta { display: flex; gap: 6px; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.pri { font-size: 10px; padding: 1px 6px; border-radius: 8px; border: 1px solid #3a3d42; }
.pri.high { color: #e05c5c; border-color: #e05c5c; }
.pri.low { color: #9aa0a6; }
.assign { font-size: 11px; max-width: 130px; }
.card-nav { display: flex; gap: 4px; justify-content: flex-end; }
.intake { padding: 10px; border-top: 1px solid #3a3d42; display: flex; flex-direction: column; gap: 6px; }
.mini { font-size: 12px; padding: 3px 8px; border: 1px solid #3a3d42; background: #2b2e33; color: #e8e8e8; border-radius: 5px; cursor: pointer; }
</style>
