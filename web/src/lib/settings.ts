// Runtime settings. Models are interchangeable (prd.md constraint): a tier
// resolves to an Ollama model here, never in engine code. Nothing below is a
// hard dependency on a specific model — these are defaults the user overrides
// in the Settings panel, validated against GET /api/tags.

export type Tier = "reason" | "build" | "cheap";

export interface Settings {
  /** Ollama origin. In dev the Vite proxy serves it at /ollama. */
  ollamaOrigin: string;
  /** tier -> Ollama model name (7B–30B target range). */
  tierModels: Record<Tier, string>;
  /** re-queue cap: how many times Opsec/legal may send the goal back. */
  requeueCap: number;
  /** soft per-cycle token-growth target, reported not clamped (~500–1000). */
  cycleTokenTarget: [number, number];
  /** temperature for persona turns. */
  temperature: number;
}

export const DEFAULT_SETTINGS: Settings = {
  // Same-origin proxy path (vite.config.ts). Set to a full URL to hit Ollama
  // directly (requires OLLAMA_ORIGIN / CORS).
  ollamaOrigin: "/ollama",
  tierModels: {
    reason: "qwen2.5:32b",
    build: "qwen2.5:14b",
    cheap: "qwen2.5:7b",
  },
  requeueCap: 2,
  cycleTokenTarget: [500, 1000],
  temperature: 0.4,
};

// Persona frontmatter uses opus/sonnet/haiku (or a concrete id). Map those
// reasoning tiers onto our three Ollama tiers. Unknown -> build.
const ALIAS_TO_TIER: Record<string, Tier> = {
  opus: "reason",
  "claude-opus-4-8": "reason",
  reason: "reason",
  sonnet: "build",
  "claude-sonnet-5": "build",
  build: "build",
  haiku: "cheap",
  fable: "cheap",
  cheap: "cheap",
};

export function tierForModelAlias(alias: string): Tier {
  // Some charters write "sonnet (build)" etc.; take the first token.
  const key = alias.split(/[\s(]/)[0].trim();
  return ALIAS_TO_TIER[key] ?? "build";
}
