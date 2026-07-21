// The execution loop: the *how it runs* graph that the final meta-prompt
// emits alongside the plan. It shows agents spun in parallel, sequential
// handoffs, and gates (lint/test) that loop back to an agent on failure and
// advance on success, ending in "Prep PR".
//
// The model may emit a loop spec (```loop JSON); if it's missing or invalid
// we build a sensible default from the run's participants + standard gates.
// Either way the spec is compiled to Mermaid deterministically, so the
// rendered diagram is always valid.

export type LoopNodeKind = "start" | "agent" | "gate" | "terminal";
export type LoopEdgeType = "seq" | "parallel" | "pass" | "fail";

export interface LoopNode {
  id: string;
  label: string;
  kind: LoopNodeKind;
}
export interface LoopEdge {
  from: string;
  to: string;
  type: LoopEdgeType;
  label?: string;
}
export interface LoopSpec {
  nodes: LoopNode[];
  edges: LoopEdge[];
}

const KINDS: LoopNodeKind[] = ["start", "agent", "gate", "terminal"];
const EDGE_TYPES: LoopEdgeType[] = ["seq", "parallel", "pass", "fail"];

/** A mermaid-safe id: alphanumerics + underscore. */
function safeId(raw: string): string {
  return raw.replace(/[^A-Za-z0-9_]/g, "_") || "n";
}
/** A mermaid-safe quoted label. */
function safeLabel(raw: string): string {
  return raw.replace(/["\n\r]/g, " ").trim().slice(0, 40) || "?";
}

/** Compile a loop spec into a valid Mermaid flowchart. */
export function compileLoopToMermaid(spec: LoopSpec): string {
  const lines = ["flowchart LR"];
  const idmap = new Map<string, string>();
  for (const n of spec.nodes) {
    const id = safeId(n.id);
    idmap.set(n.id, id);
    const label = safeLabel(n.label);
    if (n.kind === "start") lines.push(`  ${id}(("${label}"))`);
    else if (n.kind === "gate") lines.push(`  ${id}{"${label}"}`);
    else if (n.kind === "terminal") lines.push(`  ${id}(["${label}"])`);
    else lines.push(`  ${id}["${label}"]`);
  }
  for (const e of spec.edges) {
    const from = idmap.get(e.from);
    const to = idmap.get(e.to);
    if (!from || !to) continue; // skip edges to unknown nodes
    const lbl = e.label ? `|"${safeLabel(e.label)}"|` : "";
    // Failures loop back on a dotted line; everything else is solid.
    const arrow = e.type === "fail" ? "-.->" : "-->";
    lines.push(`  ${from} ${arrow}${lbl} ${to}`);
  }
  return lines.join("\n");
}

/**
 * Build the default execution loop from the run's participants: the first two
 * agents spin in parallel, the rest hand off sequentially, then a lint gate
 * (fail → back to the last agent, pass → test), a test gate (fail → back,
 * pass → prep PR).
 */
export function defaultLoop(agentLabels: string[]): LoopSpec {
  const labels = agentLabels.length ? agentLabels : ["implementer"];
  const agents: LoopNode[] = labels.map((label, i) => ({ id: `ag${i}`, label, kind: "agent" }));
  const nodes: LoopNode[] = [
    { id: "start", label: "Goal", kind: "start" },
    ...agents,
    { id: "lint", label: "Lint", kind: "gate" },
    { id: "test", label: "Test", kind: "gate" },
    { id: "pr", label: "Prep PR", kind: "terminal" },
  ];
  const edges: LoopEdge[] = [];
  let feeders: string[];

  if (agents.length >= 2) {
    edges.push({ from: "start", to: "ag0", type: "parallel" });
    edges.push({ from: "start", to: "ag1", type: "parallel" });
    if (agents.length > 2) {
      edges.push({ from: "ag0", to: "ag2", type: "seq" });
      edges.push({ from: "ag1", to: "ag2", type: "seq" });
      for (let i = 2; i < agents.length - 1; i++) {
        edges.push({ from: `ag${i}`, to: `ag${i + 1}`, type: "seq" });
      }
      feeders = [`ag${agents.length - 1}`];
    } else {
      feeders = ["ag0", "ag1"];
    }
  } else {
    edges.push({ from: "start", to: "ag0", type: "seq" });
    feeders = ["ag0"];
  }

  const loopTarget = feeders[feeders.length - 1];
  for (const f of feeders) edges.push({ from: f, to: "lint", type: "seq" });
  edges.push({ from: "lint", to: loopTarget, type: "fail", label: "lint fails" });
  edges.push({ from: "lint", to: "test", type: "pass", label: "lint ok" });
  edges.push({ from: "test", to: loopTarget, type: "fail", label: "tests fail" });
  edges.push({ from: "test", to: "pr", type: "pass", label: "green" });
  return { nodes, edges };
}

/** Extract a loop spec from a ```loop / ```json fenced block, if valid. */
export function parseLoopSpec(text: string): LoopSpec | null {
  const fence = text.match(/```(?:loop|json)\s*([\s\S]*?)```/i);
  const raw = fence ? fence[1] : null;
  if (!raw) return null;
  let obj: unknown;
  try {
    obj = JSON.parse(raw);
  } catch {
    return null;
  }
  const spec = (obj as { loop?: unknown }).loop ?? obj;
  if (!spec || typeof spec !== "object") return null;
  const s = spec as { nodes?: unknown; edges?: unknown };
  if (!Array.isArray(s.nodes) || !Array.isArray(s.edges)) return null;

  const nodes: LoopNode[] = [];
  for (const n of s.nodes) {
    if (!n || typeof n !== "object") return null;
    const nn = n as Record<string, unknown>;
    if (typeof nn.id !== "string" || typeof nn.label !== "string") return null;
    const kind = KINDS.includes(nn.kind as LoopNodeKind) ? (nn.kind as LoopNodeKind) : "agent";
    nodes.push({ id: nn.id, label: nn.label, kind });
  }
  const edges: LoopEdge[] = [];
  for (const e of s.edges) {
    if (!e || typeof e !== "object") return null;
    const ee = e as Record<string, unknown>;
    if (typeof ee.from !== "string" || typeof ee.to !== "string") return null;
    const type = EDGE_TYPES.includes(ee.type as LoopEdgeType) ? (ee.type as LoopEdgeType) : "seq";
    edges.push({ from: ee.from, to: ee.to, type, label: typeof ee.label === "string" ? ee.label : undefined });
  }
  if (!nodes.length) return null;
  return { nodes, edges };
}

/** Remove the ```loop fenced block from the plan text shown to the user. */
export function stripLoopBlock(text: string): string {
  return text.replace(/```(?:loop|json)\s*[\s\S]*?```/i, "").trim();
}
