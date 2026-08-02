<script setup lang="ts">
import { ref, onMounted, nextTick } from "vue";
import { api, type ChatRoom, type ChatMessage, type SummonState } from "../api";

const rooms = ref<ChatRoom[]>([]);
const active = ref<ChatRoom | null>(null);
const messages = ref<ChatMessage[]>([]);
const draft = ref("");
const summonPrompt = ref("");
const summon = ref<SummonState | null>(null);
const summonBusy = ref(false);
const notice = ref("");
const replyId = ref("");
const body = ref<HTMLElement | null>(null);

onMounted(async () => { rooms.value = await api.chatRooms(); });

async function openRoom(r: ChatRoom) {
  active.value = r;
  replyId.value = r.agents[0]?.id ?? "";
  notice.value = "";
  [messages.value, summon.value] = await Promise.all([
    api.chatHistory(r.team), api.getSummon(r.team),
  ]);
  scroll();
}
function scroll() { nextTick(() => body.value?.scrollTo({ top: body.value.scrollHeight })); }

const summonActive = () => summon.value?.state === "active";

async function send() {
  if (!active.value || !draft.value.trim()) return;
  messages.value.push(await api.chatPost(active.value.team, draft.value));
  draft.value = "";
  scroll();
}

// Feature 1: model-driven summon, one active per room.
async function doSummon() {
  if (!active.value || !summonPrompt.value.trim() || summonActive()) return;
  summonBusy.value = true;
  notice.value = "";
  try {
    const res = await api.summon(active.value.team, summonPrompt.value);
    if (!res.ok) { notice.value = res.message; return; }
    summon.value = res.summon;
    summonPrompt.value = "";
    if (res.summon.state === "failed") notice.value = res.summon.message;
    else if (res.summon.state === "complete") notice.value = res.summon.message; // no agents needed
    messages.value = await api.chatHistory(active.value.team); // pick up the "Summoned: …" line
    scroll();
  } finally {
    summonBusy.value = false;
  }
}
async function endSummon() {
  if (!active.value) return;
  summon.value = await api.completeSummon(active.value.team);
}
async function reply() {
  if (!active.value || !replyId.value) return;
  try {
    messages.value.push(await api.chatReply(active.value.team, replyId.value));
    scroll();
  } catch (e) { notice.value = (e as Error).message; }
}
</script>

<template>
  <div class="chats">
    <aside class="rooms">
      <div class="rooms-head">Teams</div>
      <button v-for="r in rooms" :key="r.team" class="room" :class="{ active: active?.team === r.team }" @click="openRoom(r)">
        <span>{{ r.team }}</span>
        <span class="right"><span v-if="r.summon_active" class="live">●</span>{{ r.agent_count }}</span>
      </button>
    </aside>

    <section v-if="active" class="room-view">
      <header class="room-head">
        # {{ active.team }} · {{ active.agent_count }} agents
        <span v-if="summonActive()" class="badge-active" data-testid="summon-active">● Summon Active</span>
        <button v-if="summonActive()" class="mini" @click="endSummon">Complete</button>
      </header>

      <div ref="body" class="msgs">
        <div v-for="m in messages" :key="m.id" class="msg" :class="m.sender === 'user' ? 'me' : 'agent'">
          <div v-if="m.sender === 'agent'" class="who">{{ m.agent_id }}</div>
          <div class="bubble">{{ m.content }}</div>
        </div>
        <p v-if="!messages.length" class="empty">No messages yet. Summon agents or say something.</p>
      </div>

      <p v-if="notice" class="notice" data-testid="summon-notice">{{ notice }}</p>

      <div class="summon-bar">
        <input v-model="summonPrompt" :disabled="summonActive() || summonBusy"
               data-testid="summon-input" placeholder="Describe the task to summon agents for…" />
        <button class="mini summon" :disabled="summonActive() || summonBusy || !summonPrompt.trim()"
                data-testid="summon-btn" @click="doSummon">
          {{ summonBusy ? "Summoning…" : summonActive() ? "Summon Active" : "Summon" }}
        </button>
      </div>

      <div class="composer">
        <input v-model="draft" placeholder="Message…" @keydown.enter="send" />
        <button class="mini" @click="send">Send</button>
        <template v-if="summonActive() && summon?.selected_agents.length">
          <select v-model="replyId">
            <option v-for="id in summon!.selected_agents" :key="id" :value="id">{{ id }}</option>
          </select>
          <button class="mini reply" @click="reply">Reply</button>
        </template>
      </div>
    </section>
    <section v-else class="empty-room"><p>Pick a team to enter its breakout room.</p></section>
  </div>
</template>

<style scoped>
.chats { display: grid; grid-template-columns: 200px 1fr; height: 100%; }
.rooms { border-right: 1px solid #3a3d42; overflow-y: auto; padding: 10px; }
.rooms-head { text-transform: uppercase; font-size: 11px; color: #9aa0a6; margin: 6px 6px 8px; }
.room { display: flex; justify-content: space-between; width: 100%; text-align: left; background: transparent; border: none; color: #e8e8e8; padding: 8px; border-radius: 6px; cursor: pointer; }
.room:hover { background: #2b2e33; }
.room.active { background: #2b2e33; color: #4a9eff; }
.right { color: #9aa0a6; font-size: 12px; display: flex; gap: 5px; align-items: center; }
.live { color: #2eb67d; font-size: 9px; }
.room-view { display: flex; flex-direction: column; min-height: 0; }
.room-head { padding: 12px 16px; border-bottom: 1px solid #3a3d42; font-weight: 600; display: flex; align-items: center; gap: 10px; }
.badge-active { font-size: 11px; color: #2eb67d; border: 1px solid #2eb67d; border-radius: 10px; padding: 1px 8px; }
.msgs { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 8px; }
.msg { max-width: 70%; }
.msg.me { align-self: flex-end; }
.msg.agent { align-self: flex-start; }
.who { font-size: 11px; color: #9aa0a6; margin-bottom: 2px; }
.bubble { padding: 8px 12px; border-radius: 14px; white-space: pre-wrap; line-height: 1.4; }
.msg.me .bubble { background: #4a9eff; color: #06203d; border-bottom-right-radius: 4px; }
.msg.agent .bubble { background: #2b2e33; border: 1px solid #3a3d42; border-bottom-left-radius: 4px; }
.empty, .empty-room { color: #9aa0a6; }
.empty-room { display: flex; align-items: center; justify-content: center; }
.notice { color: #e0a33e; font-size: 12px; padding: 6px 16px; margin: 0; }
.summon-bar { display: flex; gap: 8px; padding: 8px 16px; border-top: 1px solid #3a3d42; }
.summon-bar input { flex: 1; }
.composer { display: flex; gap: 8px; padding: 12px 16px; border-top: 1px solid #3a3d42; }
.composer input { flex: 1; }
.mini { font-size: 12px; padding: 4px 10px; border: 1px solid #3a3d42; background: #2b2e33; color: #e8e8e8; border-radius: 5px; cursor: pointer; }
.mini:disabled { opacity: 0.5; cursor: not-allowed; }
.mini.summon { background: #b07be0; color: #1a0d2e; border-color: #b07be0; }
.mini.reply { background: #4a9eff; color: #06203d; border-color: #4a9eff; }
</style>
