// Thin API client for the FastAPI backend.
export interface Sprint { id: number; name: string }
export interface Project { id: number; name: string; sprints: Sprint[] }
export interface DocMeta { id: number; doc_type: string; title: string }
export interface Doc extends DocMeta { sprint_id: number; content: string; updated_at: string }
export interface LibraryItem { type: string; label: string; category: string }
export interface AgentStatus { available: boolean; models: string[]; endpoint: string }
export interface Stage { id: string; label: string }
export interface Issue {
  id: number; title: string; description: string; priority: string;
  tags: string; stage: string; project_id: number | null;
}
export interface AgentInfo { id: string; title: string; team: string }
export interface AgentTeam { team: string; agents: AgentInfo[] }
export interface QueueItem {
  id: number; agent_id: string; target_kind: string; target_id: number;
  note: string; priority: number; position: number; state: string;
  attempts: number; last_error: string;
}
export interface ZettelTemplate { id: string; label: string; priority: string; description: string }
export interface ChatRoom { team: string; agent_count: number; agents: AgentInfo[]; last_message_at: string | null }
export interface ChatMessage { id: number; room: string; sender: string; agent_id: string | null; content: string; created_at: string }

async function j<T>(r: Response): Promise<T> {
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json() as Promise<T>;
}

export const api = {
  projects: () => fetch("/api/projects").then(j<Project[]>),
  createProject: (name: string) =>
    fetch("/api/projects", { method: "POST", headers: h(), body: JSON.stringify({ name }) }).then(j<Project>),
  createSprint: (project_id: number, name: string) =>
    fetch("/api/sprints", { method: "POST", headers: h(), body: JSON.stringify({ project_id, name }) }).then(j<Sprint>),
  documents: (sprintId: number) =>
    fetch(`/api/sprints/${sprintId}/documents`).then(j<DocMeta[]>),
  createDocument: (sprint_id: number, doc_type: string, title?: string) =>
    fetch("/api/documents", { method: "POST", headers: h(), body: JSON.stringify({ sprint_id, doc_type, title }) }).then(j<Doc>),
  document: (id: number) => fetch(`/api/documents/${id}`).then(j<Doc>),
  saveDocument: (id: number, content: string, title?: string) =>
    fetch(`/api/documents/${id}`, { method: "PUT", headers: h(), body: JSON.stringify({ content, title }) }).then(j<Doc>),
  library: () => fetch("/api/doc-library").then(j<LibraryItem[]>),
  agentStatus: () => fetch("/api/agent/status").then(j<AgentStatus>),
  stages: () => fetch("/api/kanban/stages").then(j<Stage[]>),
  issues: () => fetch("/api/issues").then(j<Issue[]>),
  createIssue: (title: string, priority = "medium", tags = "") =>
    fetch("/api/issues", { method: "POST", headers: h(), body: JSON.stringify({ title, priority, tags }) }).then(j<Issue>),
  updateIssue: (id: number, patch: { stage?: string; project_id?: number | null; priority?: string }) =>
    fetch(`/api/issues/${id}`, { method: "PUT", headers: h(), body: JSON.stringify(patch) }).then(j<Issue>),
  agents: () => fetch("/api/agents").then(j<{ teams: AgentTeam[]; count: number }>),
  // Agent-Queue
  queue: () => fetch("/api/queue").then(j<QueueItem[]>),
  enqueue: (agent_id: string, target_id: number, note = "", priority = 0) =>
    fetch("/api/queue", { method: "POST", headers: h(), body: JSON.stringify({ agent_id, target_id, note, priority }) }).then(j<QueueItem>),
  manageQueue: (id: number, patch: { priority?: number; state?: string; agent_id?: string }) =>
    fetch(`/api/queue/${id}`, { method: "PUT", headers: h(), body: JSON.stringify(patch) }).then(j<QueueItem>),
  processQueue: (id: number) =>
    fetch(`/api/queue/${id}/process`, { method: "POST", headers: h() }).then(j<QueueItem>),
  // Zettlebucket
  zettelTemplates: () => fetch("/api/zettel/templates").then(j<ZettelTemplate[]>),
  zettelSubmit: (b: { title: string; description?: string; priority?: string; tags?: string }) =>
    fetch("/api/zettel/submit", { method: "POST", headers: h(), body: JSON.stringify(b) }).then(j<Issue>),
  // Chats
  chatRooms: () => fetch("/api/chats/rooms").then(j<ChatRoom[]>),
  chatHistory: (room: string) => fetch(`/api/chats/${room}/messages`).then(j<ChatMessage[]>),
  chatPost: (room: string, content: string) =>
    fetch(`/api/chats/${room}/messages`, { method: "POST", headers: h(), body: JSON.stringify({ content }) }).then(j<ChatMessage>),
  chatSummon: (room: string, agent_id: string) =>
    fetch(`/api/chats/${room}/summon`, { method: "POST", headers: h(), body: JSON.stringify({ agent_id }) }).then(j<ChatMessage>),
  agentAssist: (id: number, selection: string, instruction: string, agent_ids: string[]) =>
    fetch(`/api/documents/${id}/agent-assist`, { method: "POST", headers: h(), body: JSON.stringify({ selection, instruction, agent_ids }) })
      .then(j<{ results: { agent: string; text?: string; error?: string }[] }>),
};

function h() {
  return { "Content-Type": "application/json" };
}
