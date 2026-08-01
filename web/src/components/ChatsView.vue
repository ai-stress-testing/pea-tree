<script setup lang="ts">
import { ref, onMounted, nextTick } from "vue";
import { api, type ChatRoom, type ChatMessage } from "../api";

const rooms = ref<ChatRoom[]>([]);
const active = ref<ChatRoom | null>(null);
const messages = ref<ChatMessage[]>([]);
const draft = ref("");
const summonId = ref("");
const body = ref<HTMLElement | null>(null);

onMounted(async () => { rooms.value = await api.chatRooms(); });

async function openRoom(r: ChatRoom) {
  active.value = r;
  summonId.value = r.agents[0]?.id ?? "";
  messages.value = await api.chatHistory(r.team);
  scroll();
}
async function send() {
  if (!active.value || !draft.value.trim()) return;
  messages.value.push(await api.chatPost(active.value.team, draft.value));
  draft.value = "";
  scroll();
}
async function summon() {
  if (!active.value || !summonId.value) return;
  try {
    messages.value.push(await api.chatSummon(active.value.team, summonId.value));
    scroll();
  } catch { /* model offline */ }
}
function scroll() {
  nextTick(() => body.value?.scrollTo({ top: body.value.scrollHeight }));
}
</script>

<template>
  <div class="chats">
    <aside class="rooms">
      <div class="rooms-head">Teams</div>
      <button
        v-for="r in rooms"
        :key="r.team"
        class="room"
        :class="{ active: active?.team === r.team }"
        @click="openRoom(r)"
      >
        <span>{{ r.team }}</span>
        <span class="agent-count">{{ r.agent_count }}</span>
      </button>
    </aside>

    <section v-if="active" class="room-view">
      <header class="room-head"># {{ active.team }} · {{ active.agent_count }} agents</header>
      <div ref="body" class="msgs">
        <div
          v-for="m in messages"
          :key="m.id"
          class="msg"
          :class="m.sender === 'user' ? 'me' : 'agent'"
        >
          <div v-if="m.sender === 'agent'" class="who">{{ m.agent_id }}</div>
          <div class="bubble">{{ m.content }}</div>
        </div>
        <p v-if="!messages.length" class="empty">No messages yet. Say something, or summon an agent.</p>
      </div>
      <div class="composer">
        <input v-model="draft" placeholder="Message…" @keydown.enter="send" />
        <button class="mini" @click="send">Send</button>
        <select v-model="summonId">
          <option v-for="a in active.agents" :key="a.id" :value="a.id">{{ a.title }}</option>
        </select>
        <button class="mini summon" @click="summon">Summon</button>
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
.agent-count { color: #9aa0a6; font-size: 12px; }
.room-view { display: flex; flex-direction: column; min-height: 0; }
.room-head { padding: 12px 16px; border-bottom: 1px solid #3a3d42; font-weight: 600; }
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
.composer { display: flex; gap: 8px; padding: 12px 16px; border-top: 1px solid #3a3d42; }
.composer input { flex: 1; }
.mini { font-size: 12px; padding: 4px 10px; border: 1px solid #3a3d42; background: #2b2e33; color: #e8e8e8; border-radius: 5px; cursor: pointer; }
.mini.summon { background: #b07be0; color: #1a0d2e; border-color: #b07be0; }
</style>
