// The iterative groupchat engine (iterative-groupchat spec, sub-issue 3).
//
//   message -> select participants -> ordered iterate (fresh context)
//           -> (re-queue by Opsec/legal) -> synthesize final
//
// Personas come from the generated roster manifest, so adding a role under
// agents/ makes it selectable with no edit here.

import { OllamaClient } from "./ollama";
import { Settings, Tier, tierForModelAlias } from "./settings";
import { PERSONAS, PERSONA_BY_ID, Persona } from "../generated/personas";

export interface Turn {
  id: string;
  personaId: string;
  name: string;
  cycle: number;
  text: string;
  tokenCost: number;
  requeued: boolean;
}

export type { RunTotals } from "./store/types";
import type { RunTotals } from "./store/types";

export type RunEvent =
  | { type: "participants"; ids: string[] }
  | { type: "turn-start"; turn: Turn }
  | { type: "turn-token"; id: string; chunk: string }
  | { type: "turn-end"; turn: Turn; cycleTokens: number; withinTarget: boolean }
  | { type: "requeue"; by: string; target: string; accepted: boolean }
  | { type: "final-start" }
  | { type: "final-token"; chunk: string }
  | { type: "final-end"; final: string; totals: RunTotals }
  | { type: "error"; message: string };

// Roles that may send the goal back to an earlier agent (issue #5).
const REQUEUE_ROLES = new Set(["security/senior-secops", "legal/product-counsel"]);

// Run order tuned to issue #5: PM opens, builders/consultants in the middle,
// the adversary near the end, then Opsec and legal last (they gate + re-queue).
function queueRank(p: Persona): number {
  const byId: Record<string, number> = {
    "pm/project-manager": 0,
    "pm/ticket-workflow-steward": 1,
    "logicians/software-architect": 2,
    "ai/multi-agent-systems-architect": 2,
    "ai/prompt-engineer": 4,
    "logicians/falsifier": 6,
    "security/senior-secops": 7,
    "legal/product-counsel": 8,
  };
  if (p.id in byId) return byId[p.id];
  const byTeam: Record<string, number> = {
    pm: 1, backend: 3, frontend: 4, testing: 5,
  };
  return byTeam[p.team] ?? 5;
}

const mentionRe = /@([a-z][a-z0-9]*\/[a-z0-9-]+)/g;

export class Groupchat {
  private client: OllamaClient;
  private tierModel: Record<Tier, string> = { reason: "", build: "", cheap: "" };

  constructor(private settings: Settings) {
    this.client = new OllamaClient(settings.ollamaOrigin);
  }

  private modelFor(p: Persona): string {
    return this.tierModel[tierForModelAlias(p.model)];
  }

  /** Resolve each tier to a model actually present in Ollama. */
  private async resolveTiers(emit: (e: RunEvent) => void): Promise<void> {
    for (const tier of ["reason", "build", "cheap"] as Tier[]) {
      const r = await this.client.resolveModel(this.settings.tierModels[tier]);
      this.tierModel[tier] = r.model;
      if (r.fellBack) {
        emit({
          type: "error",
          message: `tier "${tier}": ${this.settings.tierModels[tier]} not pulled, using ${r.model}`,
        });
      }
    }
  }

  private mentions(message: string): string[] {
    const out: string[] = [];
    for (const m of message.matchAll(mentionRe)) {
      if (PERSONA_BY_ID[m[1]]) out.push(m[1]);
    }
    return out;
  }

  /** LLM router: pick the roles a request needs, over the roster manifest. */
  private async route(message: string, signal?: AbortSignal): Promise<string[]> {
    const roster = PERSONAS.map((p) => `- ${p.id}: ${p.description}`).join("\n");
    try {
      const { text } = await this.client.chat({
        model: this.tierModel.cheap,
        temperature: 0,
        signal,
        messages: [
          {
            role: "system",
            content:
              "You are a router for a planning groupchat. Given a request and a " +
              "roster, choose the 3 to 6 roles whose expertise the request needs. " +
              "Reply with ONLY a JSON array of role id strings, nothing else.",
          },
          { role: "user", content: `REQUEST:\n${message}\n\nROSTER:\n${roster}` },
        ],
      });
      const m = text.match(/\[[\s\S]*?\]/);
      if (m) {
        const ids = JSON.parse(m[0]) as unknown;
        if (Array.isArray(ids)) {
          return ids.filter((x): x is string => typeof x === "string" && !!PERSONA_BY_ID[x]);
        }
      }
    } catch {
      /* fall through to default */
    }
    return [];
  }

  /** mentions ∪ router, else a sane default; ordered by queue rank. */
  private async selectParticipants(message: string, signal?: AbortSignal): Promise<string[]> {
    const mentioned = this.mentions(message);
    let ids = [...mentioned];
    const routed = await this.route(message, signal);
    for (const id of routed) if (!ids.includes(id)) ids.push(id);
    if (ids.length === 0) {
      ids = [
        "pm/project-manager",
        "logicians/software-architect",
        "security/senior-secops",
        "legal/product-counsel",
      ].filter((id) => PERSONA_BY_ID[id]);
    }
    return ids
      .map((id) => PERSONA_BY_ID[id])
      .sort((a, b) => queueRank(a) - queueRank(b))
      .map((p) => p.id);
  }

  private digest(turns: Turn[]): string {
    if (!turns.length) return "(none yet — you are first)";
    return turns
      .map((t) => `- ${t.personaId} (cycle ${t.cycle}): ${t.text.replace(/\s+/g, " ").slice(0, 220)}`)
      .join("\n");
  }

  private turnMessages(p: Persona, goal: string, prior: Turn[]) {
    const canRequeue = REQUEUE_ROLES.has(p.id);
    const system =
      p.charter +
      "\n\n---\nYou are one voice in an iterative planning groupchat. In 180 words " +
      "or fewer, contribute a short paragraph or a bulleted list of concrete goals/" +
      "constraints from YOUR expertise for the initial goal. Build on prior turns; " +
      "do not restate them." +
      (canRequeue
        ? " If and only if an earlier plan has a real blocker in your domain, you " +
          "may add ONE final line exactly `REQUEUE: <team/role>` naming the earlier " +
          "agent that must revisit it."
        : "");
    const user =
      `INITIAL GOAL:\n${goal}\n\nPRIOR TURNS (digest):\n${this.digest(prior)}\n\n` +
      `Your turn as ${p.name}:`;
    return [
      { role: "system" as const, content: system },
      { role: "user" as const, content: user },
    ];
  }

  private parseRequeue(text: string): string | null {
    const m = text.match(/REQUEUE:\s*([a-z][a-z0-9]*\/[a-z0-9-]+)/i);
    if (m && PERSONA_BY_ID[m[1]]) return m[1];
    return null;
  }

  /**
   * Run the groupchat. Streams progress via `emit`; resolves when the final
   * result is produced (or an unrecoverable error is emitted).
   */
  async run(goal: string, emit: (e: RunEvent) => void, signal?: AbortSignal): Promise<void> {
    try {
      await this.resolveTiers(emit);
    } catch (e) {
      emit({ type: "error", message: (e as Error).message });
      return;
    }

    const queue = await this.selectParticipants(goal, signal);
    emit({ type: "participants", ids: queue });

    const turns: Turn[] = [];
    let requeues = 0;
    let cycle = 0;
    let totalTokens = 0;
    const [lo, hi] = this.settings.cycleTokenTarget;

    // queue is mutable: a re-queue splices a role in after the current index.
    for (let i = 0; i < queue.length; i++) {
      if (signal?.aborted) return;
      const persona = PERSONA_BY_ID[queue[i]];
      cycle += 1;
      const requeued = i > 0 && turns.some((t) => t.personaId === persona.id);
      const turn: Turn = {
        id: `${persona.id}#${cycle}`,
        personaId: persona.id,
        name: persona.name,
        cycle,
        text: "",
        tokenCost: 0,
        requeued,
      };
      emit({ type: "turn-start", turn: { ...turn } });

      let result;
      try {
        result = await this.client.chat({
          model: this.modelFor(persona),
          temperature: this.settings.temperature,
          signal,
          messages: this.turnMessages(persona, goal, turns),
          onToken: (chunk) => {
            turn.text += chunk;
            emit({ type: "turn-token", id: turn.id, chunk });
          },
        });
      } catch (e) {
        if (signal?.aborted) return;
        emit({ type: "error", message: `${persona.id}: ${(e as Error).message}` });
        continue;
      }

      turn.text = result.text;
      turn.tokenCost = result.promptTokens + result.evalTokens;
      totalTokens += turn.tokenCost;
      turns.push(turn);
      emit({
        type: "turn-end",
        turn: { ...turn },
        cycleTokens: turn.tokenCost,
        withinTarget: turn.tokenCost >= lo && turn.tokenCost <= hi,
      });

      // Opsec / legal may re-queue an earlier agent, under the cap.
      if (REQUEUE_ROLES.has(persona.id)) {
        const target = this.parseRequeue(turn.text);
        if (target) {
          const accepted = requeues < this.settings.requeueCap;
          emit({ type: "requeue", by: persona.id, target, accepted });
          if (accepted) {
            requeues += 1;
            queue.splice(i + 1, 0, target); // revisit right after this gate
          }
        }
      }
    }

    // Synthesize the final result.
    emit({ type: "final-start" });
    let final = "";
    try {
      const res = await this.client.chat({
        model: this.tierModel.reason,
        temperature: 0.3,
        signal,
        messages: [
          {
            role: "system",
            content:
              "You are the orchestrator closing an iterative planning groupchat. " +
              "Fold the turns into ONE actionable MVP plan: numbered steps, the " +
              "key constraints each specialist raised, and explicit open risks. " +
              "Be concrete; do not invent expertise no one contributed.",
          },
          { role: "user", content: `INITIAL GOAL:\n${goal}\n\nGROUPCHAT:\n${this.digest(turns)}` },
        ],
        onToken: (chunk) => {
          final += chunk;
          emit({ type: "final-token", chunk });
        },
      });
      final = res.text;
      totalTokens += res.promptTokens + res.evalTokens;
    } catch (e) {
      if (signal?.aborted) return;
      emit({ type: "error", message: `synthesis: ${(e as Error).message}` });
    }
    emit({ type: "final-end", final, totals: { tokens: totalTokens, cycles: cycle, requeues } });
  }
}
