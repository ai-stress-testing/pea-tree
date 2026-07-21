<script setup lang="ts">
import { computed } from "vue";
import type { UiTurn } from "../store";
import { PERSONA_BY_ID } from "../generated/personas";

const props = defineProps<{ turn: UiTurn }>();

const persona = computed(() => PERSONA_BY_ID[props.turn.personaId]);
const initials = computed(() => {
  const p = persona.value;
  if (!p) return "??";
  return (p.role || p.name).slice(0, 2).toUpperCase();
});
const team = computed(() => persona.value?.team ?? "");
</script>

<template>
  <div class="turn" :class="{ requeued: turn.requeued }">
    <div class="avatar" :title="team">{{ initials }}</div>
    <div class="turn-body">
      <div class="turn-head">
        <span class="turn-name">{{ turn.personaId }}</span>
        <span class="badge">cycle {{ turn.cycle }}</span>
        <span v-if="turn.requeued" class="badge requeue-badge">re-queued</span>
        <span v-if="turn.tokenCost" class="badge tok">{{ turn.tokenCost }} tok</span>
        <span v-if="turn.streaming" class="badge streaming">▍ streaming</span>
      </div>
      <div class="turn-text">{{ turn.text || "…" }}</div>
    </div>
  </div>
</template>

<style scoped>
.turn { display: flex; gap: 12px; padding: 10px 4px; border-radius: 8px; }
.turn:hover { background: var(--bg-2); }
.turn.requeued { border-left: 3px solid var(--requeue); background: rgba(176, 123, 224, 0.06); }
.avatar {
  width: 36px; height: 36px; flex-shrink: 0;
  border-radius: 8px;
  background: var(--bg-3);
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 12px; color: var(--accent);
}
.turn.requeued .avatar { color: var(--requeue); }
.turn-body { flex: 1; min-width: 0; }
.turn-head { display: flex; align-items: center; gap: 8px; margin-bottom: 3px; flex-wrap: wrap; }
.turn-name { font-weight: 600; }
.turn-text { white-space: pre-wrap; line-height: 1.55; word-break: break-word; }
.tok { color: var(--accent-2); }
.streaming { color: var(--accent); }
.requeue-badge { color: var(--requeue); border-color: var(--requeue); }
</style>
