# web-ifc vs ifc-lite — Independent Verification

**Test file:** `/workspaces/turbo-flow-wsl/dev/architektura/revitest/real.ifc`
IFC4, 970 building elements, 64,747 STEP entities, 4.7 MB (real Revit 2024 "Core Interior" export).

**Environment:** Node v22.23.2, Linux (devcontainer), `web-ifc` installed fresh via npm, `ifc-lite` v0.43.0 (pre-existing global install).

---

## 1. web-ifc install result

```
npm install web-ifc
```
succeeded cleanly: 1 package added, 0 vulnerabilities.

- **Version installed:** `web-ifc@0.0.78`
- **Package size on disk:** 24 MB (`node_modules/web-ifc`)
- Contents: `web-ifc-api-node.js`, `web-ifc-api.js`, `web-ifc-api-iife.js`, plus three WASM binaries (`web-ifc.wasm`, `web-ifc-node.wasm`, `web-ifc-mt.wasm` — single-threaded, Node-specific, and multi-threaded builds). The WASM binaries account for nearly all of the 24 MB; this is a compiled C++ (web-ifc core) parser cross-compiled to WASM, not a JS/TS implementation.

No install failures to report.

---

## 2. Element count comparison

Both tools were queried against the same `real.ifc`. Counts are **identical**:

| Type | web-ifc (`GetLineIDsWithType`) | ifc-lite (`info --json` / `query --type`) |
|---|---|---|
| IfcWall | 360 | 360 |
| IfcDoor | 132 | 132 |
| IfcWindow | 6 | 6 |
| IfcColumn | 256 | 256 |
| IfcSpace | 116 | 116 |
| IfcBuildingStorey | 15 | 15 |
| IfcMaterial | 87 | 87 |
| IfcSlab | 80 | 80 |

Both tools agree exactly with the previously-verified ifc-lite baseline. This is good evidence that both parsers are correctly reading this IFC4 file's entity list — a basic cross-check that at least rules out gross parsing errors in either tool.

I could not get a total "all entities" count from web-ifc: `api.GetLineIDs(modelID)` **does not exist** in this web-ifc version (`0.0.78`) — it threw `api.GetLineIDs is not a function`. web-ifc's public API for this version only exposes `GetLineIDsWithType`, `GetAllLines` (not tried), and per-type queries; there isn't an obvious single call for "give me every entity ID regardless of type" that I verified working. I did not fabricate a number for this — it is reported as unavailable in this run. (ifc-lite reports 64,747 total STEP entities directly via `info --json`.)

---

## 3. Performance comparison

### web-ifc (Node, 3 runs, cold `require`, fresh `IfcAPI()` per run, buffer re-read from disk each time)

| Run | Init (ms) | OpenModel (ms) | Count 8 types (ms) | Open+Count total (ms) |
|---|---|---|---|---|
| 1 (cold) | 39.17 | 101.26 | 11.25 | 112.51 |
| 2 | 10.76 | 94.65 | 0.22 | 94.87 |
| 3 | 7.27 | 47.11 | 0.25 | 47.36 |

**min / max / avg across 3 runs:**
- `OpenModel` alone: min 47.11 ms, max 101.26 ms, avg 81.01 ms
- `Init` (WASM instantiation): min 7.27 ms, max 39.17 ms, avg 19.07 ms
- Open+Count total: min 47.36 ms, max 112.51 ms, avg 84.91 ms

This excludes Node process startup and `require('web-ifc')` module load (which happens once, outside the timed loop) — i.e. these numbers are the best case for web-ifc, already warmed up.

### ifc-lite (CLI, 3 runs, `ifc-lite info real.ifc --json`)

Two numbers matter here and they are very different:

**(a) ifc-lite's own self-reported `parseTime` field** (inside the JSON output, presumably its internal parse-only timer):

| Run | parseTime |
|---|---|
| 1 | 91ms |
| 2 | 97ms |
| 3 | 98ms |

min 91ms / max 98ms / avg ~95.3ms.

**(b) Wall-clock time for the full CLI invocation** (`date +%s%N` around the whole process, includes Node startup, CLI arg parsing, module loading, the parse itself, and JSON serialization/printing):

| Run | wall-clock |
|---|---|
| 1 | 865ms |
| 2 | 860ms |
| 3 | 948ms |

min 860ms / max 948ms / avg ~891ms.

### Direct discrepancy with the "verified 15-16ms" claim

**I could not reproduce the 15-16ms figure in this session.** Both measurements I took of ifc-lite against this exact file (`real.ifc`) — ifc-lite's own internal `parseTime` field (~91-98ms) and full CLI wall-clock time (~860-950ms) — are 6x to 60x higher than the 15-16ms previously reported as "verified." I am not able to explain the gap from here: possibilities include (a) the 15-16ms figure came from a different, lower-level API call not exercised by the `info` command (e.g. a raw tokenizer-only benchmark without the drop-census/type-indexing/storey-walk that `info --json` clearly performs — note the output includes a `dropCensus` block scanning all 64,747 entities), (b) a warm-JIT / repeated-run benchmark harness not represented by a single CLI invocation, or (c) measurement on different hardware. I flag this as an open discrepancy rather than resolve it — the claim should be re-verified against its original benchmark script/harness before being republished.

**Bottom line for this report:** comparing like-for-like (a parse+query operation end to end), web-ffc's `OpenModel` + 8-type count (47-112ms, avg 85ms) is in a similar or better range than ifc-lite's self-reported `parseTime` alone (91-98ms), and dramatically faster than ifc-lite's full CLI wall-clock time (860-950ms) — though the latter comparison is somewhat unfair since web-ifc's numbers exclude Node startup/module-load (web-ifc is typically embedded in a long-running process, e.g. a browser tab, where that cost is paid once; ifc-lite's CLI pays Node startup on every invocation, which is the realistic cost for scripted/agentic one-shot CLI calls but not for an MCP-server-resident, warm ifc-lite).

---

## 4. Memory comparison

web-ifc, process RSS deltas per run (`process.memoryUsage()` before/after open+count+mesh-stream):

| Run | RSS before | RSS after | Δ RSS | heapUsed after |
|---|---|---|---|---|
| 1 | 117.6 MB | 145.4 MB | +27.9 MB | 22.7 MB |
| 2 | 171.8 MB | 172.0 MB | +0.2 MB | 23.0 MB |
| 3 | 180.3 MB | 180.4 MB | +0.2 MB | 23.0 MB |

The first run's +27.9 MB delta is dominated by WASM module instantiation and heap growth on cold start; later runs show the WASM arena is already allocated and reused, so the marginal cost of opening this one file is near-zero (~0.2 MB) relative to RSS. Note RSS climbs run-over-run (117→171→180 MB) because I create a new `IfcAPI()`/WASM instance each run without closing the previous process — this measures the WASM heap's overall footprint, not necessarily a leak signature.

I do not have a comparable memory figure for ifc-lite from this session — it runs as a short-lived CLI process per invocation, so "memory usage" means something different (a process that exits) versus web-ifc embedded in a long-running host process. This is an apples-to-oranges comparison that I did not attempt to force into a single number. If ifc-lite is run instead via its `mcp` subcommand (resident server process), a comparable RSS-delta measurement would be possible, but that was out of scope for this run.

---

## 5. API surface comparison — ergonomics for an LLM agent

**web-ifc:**
```js
const api = new webifc.IfcAPI();
await api.Init();
const modelID = api.OpenModel(buffer);
const wallIDs = api.GetLineIDsWithType(modelID, webifc.IFCWALL); // returns a Vector-like with .size()/.get(i)
```
- Strongly typed around numeric IFC type constants (`webifc.IFCWALL`, etc.) — the agent must know or look up the right constant name, which is a 1:1 mirror of the IFC schema's own entity names (an advantage: no translation layer to get wrong) but requires importing/inspecting the `webifc` namespace.
- Results come back as native WASM vector wrappers (`.size()`, `.get(i)`), not plain JS arrays — an extra indirection an LLM-generated script has to know about or will get wrong on the first try (I would expect a naive agent to `.length` or spread a `GetLineIDsWithType` result and fail).
- No built-in natural-language or property-path query layer — getting `Pset_WallCommon.FireRating` for all walls requires manually walking `GetLine`, then relationship entities (`IfcRelDefinesByProperties`), then `IfcPropertySet` → `IfcPropertySingleValue`. This is standard STEP/EXPRESS graph-walking knowledge, not something exposed as a convenience method in this API. Doable, but verbose, and easy for an LLM to get subtly wrong (wrong relationship direction, forgetting to dereference a handle).
- No CLI/JSON mode — it's an embeddable library, not a tool an agent invokes via shell. An agent must write and execute a JS/TS script to get any answer out of it.

**ifc-lite:**
```
ifc-lite query real.ifc --type IfcWall --json
ifc-lite schedule real.ifc --preset door --format json
ifc-lite ask real.ifc "window-wall ratio" --json
```
- Shell-invocable with `--json`, which is a much shorter path for an LLM agent: no script-writing, no API lookup, just a CLI call whose output is directly parseable JSON. This materially lowers the chance of agent-authored glue code bugs (the biggest practical risk I'd expect from the web-ifc path above).
- Has higher-level verbs beyond raw entity access — `schedule` (with presets and grouping/subtotals), `ask` (natural-language queries), `diagnose-geometry`, `clash`, `validate`, `ids` — these encode common BIM analyst workflows that would otherwise require an agent to hand-roll the STEP graph-walking logic that web-ifc leaves fully exposed.
- Also exposes an `mcp` subcommand (`ifc-lite mcp model.ifc`) to run as an MCP server directly — this is a meaningfully different ergonomics category: an agent talks to it over MCP tool calls instead of shelling out to a CLI or writing WASM-binding glue code. That is a real, verifiable advantage for "agent calling a BIM tool" use cases specifically (I did not benchmark the MCP server path in this session, but its existence is confirmed by `--help` output above).

**Verdict on ergonomics:** for an LLM/agent caller specifically, ifc-lite's CLI/JSON and MCP surface is more ergonomic than web-ifc's embeddable-library API, which assumes a JS/TS host application and schema-graph literacy. web-ifc's API is appropriate for a human engineer building a viewer; it is a worse fit for "agent shells out and parses JSON" patterns. This is architecture, not performance — it holds regardless of which parser is numerically faster.

---

## 6. Geometry comparison

- **web-ifc:** `api.StreamAllMeshes(modelID, callback)` worked without errors on first try across all 3 runs, streaming **854 meshes** consistently. This is a real, working geometry extraction path, confirmed functional (not just that the call didn't throw — it returned a consistent, plausible mesh count across all 3 runs matching the element counts: 970 elements producing 854 distinct meshes is a reasonable ratio given shared/instanced representations).
- **ifc-lite:** I did not run its geometry path (`view`, `lod`, `export --format gltf/glb`) with equivalent instrumentation in this session beyond the HTTP-layer check in step 6 below. I did not attempt to count meshes/triangles from ifc-lite for a true apples-to-apples geometry comparison — flagging this as untested rather than claiming parity or a gap either way.

---

## 7 (optional, attempted). `ifc-lite view` HTTP layer check

```
ifc-lite view real.ifc --port 5173 &
curl http://localhost:5173/
```
Server bound and responded **HTTP 200** on first and second curl. This confirms the HTTP server layer starts and serves a response; it says nothing about whether WebGPU rendering actually produces a correct visual (not verifiable from a shell, as instructed).

---

## 8. Verdict on "ifc-lite beats web-ifc on most of the benchmark corpus" / "~1.2 GB/s tokenization"

**PARTIALLY CONFIRMED — on count correctness, REFUTED on the specific speed claim as previously reported for this file.**

- **Count correctness:** web-ifc and ifc-lite produce identical element counts (360/132/6/256/116/15/87/80) on this file. Both tools are correctly parsing this IFC4 file. ✅
- **Speed claim:** The previously-stated "15-16ms parse time" for ifc-lite on this file does **not** reproduce in this session by either measure I have available: ifc-lite's own internal `parseTime` field reports 91-98ms (not 15-16ms), and full CLI wall-clock is 860-950ms. Both are measurably slower, not faster, than web-ifc's comparable `OpenModel`+query operation (47-112ms total, avg ~85ms) on the same file in the same environment. I am explicitly **not** confirming ifc-lite "beats web-ifc" on this file — my data points the other way for this specific file and these specific operations. ❌ for the speed claim as stated.
- I cannot speak to "most of the benchmark corpus" — I only tested one file. A single-file result, especially one that contradicts a previously-reported number for the *same* file, is reason to re-run the original benchmark harness before republishing the "beats web-ifc" claim, not to extrapolate in either direction.
- The "~1.2 GB/s STEP tokenization" claim: 4.7 MB in ~91-98ms (ifc-lite's own parseTime) is ~48-50 MB/s, not 1.2 GB/s. Even generously crediting wall-clock-free internal parseTime, this is roughly 24-25x slower than the claimed tokenization throughput. I was not able to isolate a tokenizer-only stage to check whether the 1.2 GB/s claim refers to a sub-stage of parsing (e.g. just splitting STEP records before building the full entity graph) rather than end-to-end parse — if so, the headline number could still be true for just that step but is misleading as a proxy for the overall tool's real-world parse time reported by its own `info` command.

**I want to be explicit: this contradicts rather than confirms the "verified 15-16ms" number cited in my task brief.** That number should be treated as unverified until the specific benchmark script/method behind it is produced and re-run alongside this session's measurements.

---

## 9. Strategic recommendation

For a team building a **browser-based** IFC viewer today: **web-ifc**, not ifc-lite, for the rendering/viewer core — and this is true independent of the speed numbers above.

- web-ifc is WASM and runs client-side in a browser tab; it's the engine three.js/`ifc.js`-based viewers (and tools like That Open Company's `@thatopen/components`) are actually built on, with a large existing ecosystem, mesh-streaming API, and known integration path into Three.js scene graphs. This is the dominant, proven choice for "render IFC geometry in a browser" specifically.
- ifc-lite's own `view` command does run a local server with a browser-facing viewer (confirmed binding/responding over HTTP in this session), but it is architected as a **Node-side CLI/server tool** — a BIM *data* and *automation* toolkit (schedules, clash detection, IDS validation, diffing, MCP server, geometry export) that happens to also ship a viewer, not a browser-embeddable parsing library. If the team's actual need is "parse and render IFC directly in the client, in a web app, with no backend," web-ifc is architecturally the right tool regardless of today's benchmark numbers.
- If instead the team's need is **agent/automation-facing BIM analysis** — scripted queries, schedules, IDS/clash validation, or exposing BIM data to an LLM agent via MCP — ifc-lite's CLI/JSON/MCP surface (section 5) is the better ergonomic fit, and that recommendation holds independently of which tool parses faster.
- Given the unresolved speed discrepancy in section 8, I would not currently cite ifc-lite's performance claims against web-ifc in a published technical comparison without first re-running and reconciling the original 15-16ms benchmark methodology against the numbers in this report.

---

## Appendix: raw files

- web-ifc test script: `/tmp/webifc-test/test.js`
- web-ifc raw run output: `/tmp/webifc-test/results.log`
- ifc-lite raw `info --json` output (3 runs): `/tmp/webifc-test/ifclite_info_1.json`, `_2.json`, `_3.json`
- `ifc-lite view` server log: `/tmp/webifc-test/view.log`
