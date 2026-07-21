import { describe, it, expect } from "vitest";
import { defaultLoop, compileLoopToMermaid, parseLoopSpec, stripLoopBlock } from "./loop";

describe("execution loop", () => {
  it("builds a default loop: parallel head, lint/test gates, loop-back, prep PR", () => {
    const spec = defaultLoop(["pm", "architect", "front-end"]);
    const ids = spec.nodes.map((n) => n.id);
    expect(ids).toContain("lint");
    expect(ids).toContain("test");
    expect(ids).toContain("pr");

    // First two agents spin in parallel from the start.
    const parallel = spec.edges.filter((e) => e.type === "parallel");
    expect(parallel.map((e) => e.to).sort()).toEqual(["ag0", "ag1"]);

    // Lint fails loop back to an agent; lint ok advances to test; test green -> PR.
    expect(spec.edges.some((e) => e.from === "lint" && e.type === "fail")).toBe(true);
    expect(spec.edges.some((e) => e.from === "lint" && e.to === "test" && e.type === "pass")).toBe(true);
    expect(spec.edges.some((e) => e.from === "test" && e.to === "pr" && e.type === "pass")).toBe(true);
  });

  it("compiles to valid-looking Mermaid with a dotted fail edge", () => {
    const mmd = compileLoopToMermaid(defaultLoop(["a", "b"]));
    expect(mmd.startsWith("flowchart LR")).toBe(true);
    expect(mmd).toContain('lint{"Lint"}'); // gate shape
    expect(mmd).toContain('pr(["Prep PR"])'); // terminal shape
    expect(mmd).toMatch(/-\.->/); // dotted loop-back edge for failure
  });

  it("degrades to a single-agent loop", () => {
    const spec = defaultLoop([]);
    expect(spec.nodes.some((n) => n.id === "ag0")).toBe(true);
    expect(spec.edges.some((e) => e.from === "start" && e.to === "ag0")).toBe(true);
  });

  it("parses a model-emitted ```loop block and strips it from the plan", () => {
    const text =
      "Here is the plan.\n\n```loop\n" +
      JSON.stringify({
        nodes: [
          { id: "ag0", label: "dev", kind: "agent" },
          { id: "lint", label: "Lint", kind: "gate" },
        ],
        edges: [{ from: "ag0", to: "lint", type: "seq" }],
      }) +
      "\n```";
    const spec = parseLoopSpec(text);
    expect(spec).not.toBeNull();
    expect(spec!.nodes.map((n) => n.id)).toEqual(["ag0", "lint"]);
    expect(stripLoopBlock(text)).toBe("Here is the plan.");
  });

  it("returns null for a missing or malformed loop block", () => {
    expect(parseLoopSpec("no block here")).toBeNull();
    expect(parseLoopSpec("```loop\nnot json\n```")).toBeNull();
    expect(parseLoopSpec("```loop\n{}\n```")).toBeNull();
  });
});
