// Thin API client for the FastAPI backend.
export interface Sprint { id: number; name: string }
export interface Project { id: number; name: string; sprints: Sprint[] }
export interface DocMeta { id: number; doc_type: string; title: string }
export interface Doc extends DocMeta { sprint_id: number; content: string; updated_at: string }
export interface LibraryItem { type: string; label: string }
export interface AgentStatus { available: boolean; models: string[]; endpoint: string }

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
  agentAssist: (id: number, selection: string, instruction: string, agent_ids: string[]) =>
    fetch(`/api/documents/${id}/agent-assist`, { method: "POST", headers: h(), body: JSON.stringify({ selection, instruction, agent_ids }) })
      .then(j<{ results: { agent: string; text?: string; error?: string }[] }>),
};

function h() {
  return { "Content-Type": "application/json" };
}
