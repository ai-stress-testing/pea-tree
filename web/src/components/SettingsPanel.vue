<script setup lang="ts">
import { store, actions } from "../store";
import type { Tier } from "../lib/settings";

const tiers: { key: Tier; label: string; hint: string }[] = [
  { key: "reason", label: "reason", hint: "opus-tier personas + final synthesis (largest, ~30B)" },
  { key: "build", label: "build", hint: "sonnet-tier personas (~14B)" },
  { key: "cheap", label: "cheap", hint: "haiku-tier + the participant router (~7B)" },
];

function onOriginBlur() {
  actions.refreshModels();
}
</script>

<template>
  <div class="pane">
    <div class="pane-header"><strong>Settings</strong></div>
    <div class="pane-body">
      <div class="settings-grid">
        <section>
          <h3>Ollama</h3>
          <label>
            Origin
            <input v-model="store.settings.ollamaOrigin" @blur="onOriginBlur" />
          </label>
          <p class="hint">
            Dev default <code>/ollama</code> is proxied to
            <code>http://localhost:11434</code> by Vite. Status:
            <strong v-if="store.ollamaOk === true" style="color:var(--accent-2)">connected</strong>
            <strong v-else-if="store.ollamaOk === false" style="color:var(--danger)">offline</strong>
            <strong v-else>checking…</strong>
          </p>
          <button @click="actions.refreshModels()">Refresh models</button>
          <p class="hint" v-if="store.models.length">
            Pulled: <code v-for="m in store.models" :key="m" class="model-tag">{{ m }}</code>
          </p>
          <p class="hint" v-else>
            No models pulled. Try <code>ollama pull qwen2.5:7b</code>.
          </p>
        </section>

        <section>
          <h3>Tier → model</h3>
          <p class="hint">
            Personas declare a tier (opus/sonnet/haiku); each maps to an Ollama
            model here. Interchangeable — swap a model without touching code.
          </p>
          <label v-for="t in tiers" :key="t.key">
            {{ t.label }}
            <select v-if="store.models.length" v-model="store.settings.tierModels[t.key]">
              <option v-for="m in store.models" :key="m" :value="m">{{ m }}</option>
            </select>
            <input v-else v-model="store.settings.tierModels[t.key]" />
            <span class="hint">{{ t.hint }}</span>
          </label>
        </section>

        <section>
          <h3>Pipeline</h3>
          <label>
            Re-queue cap
            <input type="number" min="0" max="6" v-model.number="store.settings.requeueCap" />
            <span class="hint">how many times Opsec/legal may send the goal back</span>
          </label>
          <label>
            Temperature
            <input type="number" min="0" max="1" step="0.1" v-model.number="store.settings.temperature" />
          </label>
          <p class="hint">
            Per-cycle token target (reported, not clamped):
            {{ store.settings.cycleTokenTarget[0] }}–{{ store.settings.cycleTokenTarget[1] }}.
          </p>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-grid { display: grid; gap: 28px; max-width: 720px; }
section h3 { margin: 0 0 8px; }
label { display: flex; flex-direction: column; gap: 4px; margin-bottom: 12px; max-width: 420px; }
.hint { color: var(--muted); font-size: 12px; line-height: 1.5; }
.model-tag { margin-right: 6px; display: inline-block; margin-top: 4px; }
</style>
