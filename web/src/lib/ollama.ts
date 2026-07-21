// Typed Ollama client (iterative-groupchat spec, sub-issue 2).
// Only talks to the Ollama HTTP API. Model is always a parameter, never a
// constant — the harness must stay model-interchangeable.

export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

export interface ChatResult {
  text: string;
  promptTokens: number;
  evalTokens: number;
  model: string;
}

export interface ChatOptions {
  model: string;
  messages: ChatMessage[];
  temperature?: number;
  /** streamed token chunks, for a live Slack-like feel. */
  onToken?: (chunk: string) => void;
  /** abort a run mid-stream without leaking the reader. */
  signal?: AbortSignal;
}

export class OllamaClient {
  constructor(private origin: string) {}

  private url(path: string): string {
    return `${this.origin.replace(/\/$/, "")}${path}`;
  }

  /** Models currently pulled locally (GET /api/tags). */
  async listModels(): Promise<string[]> {
    const res = await fetch(this.url("/api/tags"));
    if (!res.ok) throw new Error(`ollama /api/tags ${res.status}`);
    const data = (await res.json()) as { models?: { name: string }[] };
    return (data.models ?? []).map((m) => m.name);
  }

  /**
   * Resolve a desired model to one that is actually present. Falls back to
   * the first available model (with `fellBack: true`) rather than failing a
   * whole run because a configured tag isn't pulled.
   */
  async resolveModel(
    desired: string,
  ): Promise<{ model: string; fellBack: boolean; available: string[] }> {
    const available = await this.listModels();
    if (available.includes(desired)) return { model: desired, fellBack: false, available };
    // tolerate a missing ":latest" suffix mismatch
    const loose = available.find((m) => m.split(":")[0] === desired.split(":")[0]);
    if (loose) return { model: loose, fellBack: loose !== desired, available };
    if (available.length) return { model: available[0], fellBack: true, available };
    throw new Error("no Ollama models available — `ollama pull qwen2.5:7b`");
  }

  /** Streamed chat completion (POST /api/chat, NDJSON). */
  async chat(opts: ChatOptions): Promise<ChatResult> {
    const res = await fetch(this.url("/api/chat"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: opts.model,
        messages: opts.messages,
        stream: true,
        options: { temperature: opts.temperature ?? 0.4 },
      }),
      signal: opts.signal,
    });
    if (!res.ok || !res.body) throw new Error(`ollama /api/chat ${res.status}`);

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    let text = "";
    let promptTokens = 0;
    let evalTokens = 0;
    try {
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        // NDJSON: one JSON object per line.
        let nl: number;
        while ((nl = buf.indexOf("\n")) >= 0) {
          const line = buf.slice(0, nl).trim();
          buf = buf.slice(nl + 1);
          if (!line) continue;
          const obj = JSON.parse(line) as {
            message?: { content?: string };
            prompt_eval_count?: number;
            eval_count?: number;
            done?: boolean;
          };
          const piece = obj.message?.content ?? "";
          if (piece) {
            text += piece;
            opts.onToken?.(piece);
          }
          if (obj.done) {
            promptTokens = obj.prompt_eval_count ?? promptTokens;
            evalTokens = obj.eval_count ?? evalTokens;
          }
        }
      }
    } finally {
      // Always release the reader, even on abort/throw.
      reader.releaseLock();
    }
    return { text, promptTokens, evalTokens, model: opts.model };
  }
}
