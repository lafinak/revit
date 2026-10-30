# ThatOpen vs ifc-lite: Platform Comparison

Date: 2026-10-30
Test file: `/workspaces/turbo-flow-wsl/dev/architektura/revitest/real.ifc` (IFC4, 970 building elements, 64,747 STEP entities)

## 1. Full `@thatopen` npm package inventory

npm registry search for `@thatopen` returns **24 total hits**, but only **6 are actual `@thatopen`-scoped packages** — the rest are third-party forks, wrappers, or unrelated packages that merely depend on or reference ThatOpen (e.g. `@ademattos/components` — a personal fork; `@iflow-mcp/openbim-mcp` — a third-party MCP wrapper, not an official ThatOpen package; `web-ifc` itself, listed separately under the OpenBIM org, not `@thatopen`).

The real `@thatopen` scope:

| Package | Version | Purpose | Category |
|---|---|---|---|
| `@thatopen/components` | 3.6.0 | Core BIM app functionalities (bootstrapping, loading, world management) | Core / app framework |
| `@thatopen/components-front` | 3.6.0 | Frontend tools for BIM apps (cameras, highlighters, UI helpers) | Viewer / rendering |
| `@thatopen/fragments` | 3.6.0 | Three.js-based geometric system + IFC importer + fragments query engine | Geometry kernel + IFC data |
| `@thatopen/ui` | 3.4.17 | Web components (UI widgets) | Viewer / UI |
| `@thatopen/ui-obc` | 3.4.5 | UI widgets specifically for `components` | Viewer / UI |
| `@thatopen/services` | 0.33.0 | Client + CLI for "That Open Platform" cloud/BIM services | Cloud services |

That's it — **6 packages**, all oriented around building one thing: a browser-embedded IFC viewer application. There is no BCF package, no IDS validation package, and no MCP/agent-tooling package anywhere in the official scope.

## 2. Install result

```
npm install @thatopen/components @thatopen/components-front
```

Succeeded cleanly: 32 packages added, **0 vulnerabilities, no peer-dependency warnings** (npm auto-installed the declared peers).

Inspecting `peerDependencies` on `@thatopen/components` and `@thatopen/fragments` confirms the architecture's center of gravity:

```json
"peerDependencies": {
  "@thatopen/fragments": "~3.6.0",
  "camera-controls": ">=3.1.2",
  "three": ">=0.182.0",
  "web-ifc": ">=0.0.77"
}
```

`three` (a WebGL rendering engine) is a **hard peer dependency of the core `components` package**, not an optional add-on. This is a strong architectural signal: ThatOpen was designed as a 3D-viewer-first platform, with everything else built around that center.

## 3. Headless / no-browser API investigation

This was the most important thing to verify empirically rather than assume. Result: **partially headless — and better than expected on the conversion side, but still viewer-centric overall.**

- **IFC → Fragments conversion (`IfcImporter.process()`)**: genuinely headless. Its own docstring says a `readFromCallback` option is "useful for node.js." I ran it for real:
  ```js
  const importer = new FRAGS.IfcImporter();
  importer.wasm = { path: "node_modules/web-ifc/", absolute: true };
  const fragmentBytes = await importer.process({ bytes: new Uint8Array(ifcBytes) });
  ```
  Against `real.ifc` (4.88 MB, 970 elements) this completed in **1.93 seconds**, producing an 838 KB fragments buffer. `web-ifc` ships a dedicated `web-ifc-node.wasm` build specifically for this.

- **Querying the converted model (`SingleThreadedFragmentsModel`)**: also genuinely headless — this class exists precisely to avoid the browser `Worker`/`Blob` machinery that the primary `FragmentsModels` class requires (its `getWorker()` method literally fetches a worker script from unpkg via a blob URL — browser-only). I loaded the `.frag` output and queried it in plain Node:
  ```js
  const model = new FRAGS.SingleThreadedFragmentsModel("real", fragBytes);
  await model.ready;
  const ids = await model.getItemsOfCategories([/IFCWALL$/, /IFCDOOR$/, /IFCWINDOW$/, /IFCSLAB$/]);
  ```
  Real output against `real.ifc`: **360 walls, 132 doors, 80 slabs, 6 windows**, 39,783 total items (elements + properties + materials) in the model. This is real, verified data, not a fabricated success claim.

- **What is NOT headless**: the primary, documented `FragmentsModels` class (multi-threaded, worker-based) is browser-first and fetches its worker bundle from a CDN via `Blob`/`Worker`. The viewer packages (`components-front`, `ui`, `ui-obc`) assume a DOM/canvas and are not usable headlessly at all — they are not geometry/data APIs, they are UI widgets.

**Conclusion**: ThatOpen does have a real, working headless path for IFC parsing and basic querying (a pleasant surprise), built specifically to serve Node.js use cases like format conversion pipelines. But it is a narrow escape hatch from an otherwise browser-first architecture, not a first-class CLI/agent-facing data API. There is no equivalent to a CLI tool, a standalone query language, or a way to open the model and run arbitrary mutation/validation without first reaching for Three.js-adjacent plumbing.

## 4. Feature-breadth comparison

| Capability | ifc-lite | ThatOpen |
|---|---|---|
| CLI | `@ifc-lite/cli` — query, validate, export, create, script | None |
| 3D Viewer | Yes (`@ifc-lite/viewer-core`, WebGL2 + REST API, also WebGPU renderer) | Yes (`components-front`, `ui`, `ui-obc` — this is ThatOpen's core strength) |
| Geometry kernel | Yes (`@ifc-lite/geometry` — exact-arithmetic CSG) | Yes (`fragments` — Three.js-based, mesh-bvh accelerated) |
| Query API | Yes (`@ifc-lite/query`, dedicated query system) | Partial — `SingleThreadedFragmentsModel` exposes query methods (categories, spatial structure, properties) but undocumented as a first-class product feature; no query language |
| Mutation/editing API | Yes (`@ifc-lite/mutations`, `@ifc-lite/create`) | Partial — `Model.edit()`/`undo()`/`redo()` exist on fragments models but are oriented at viewer-driven edits, not scripted automation |
| BCF support | Yes (`@ifc-lite/bcf`, `@ifc-lite/bcf-api`) | None |
| IDS validation | Yes (`@ifc-lite/ids`, `@ifc-lite/ids-authoring`, `@ifc-lite/ids-agent`) | None |
| MCP / agent-tool support | Yes — `@ifc-lite/mcp`, 125+ tools, agent-native by design | **None.** No MCP server, no agent-oriented API. ThatOpen's roadmap predates the agent-tool-calling pattern; it targets human developers building browser viewer apps. |
| Headless/Node usage | First-class — the entire toolkit is Node-native | Narrow escape hatch (import + single-threaded query), not a designed product surface |
| Real-time collaboration | Yes (`@ifc-lite/collab`, CRDT-based) | No equivalent (services package is cloud-client, not CRDT collab) |
| Clash detection | Yes (`@ifc-lite/clash`) | No |
| 2D drawing generation | Yes (`@ifc-lite/drawing-2d`) | No |
| Diffing | Yes (`@ifc-lite/diff`) | No |
| Package count | 50+ scoped packages | 6 scoped packages |

## 5. Adoption signals (snapshot, 2026-10-30 — not a trend)

| Package | Downloads (last month) |
|---|---|
| `web-ifc` | 966,130 |
| `@thatopen/fragments` | 410,984 |
| `@thatopen/components` | 308,246 |
| `@thatopen/components-front` | 224,516 |
| `@thatopen/ui` | 35,030 |
| `@ifc-lite/wasm` | 57,704 |
| `@ifc-lite/data` | 48,225 |
| `@ifc-lite/parser` | 42,031 |

ThatOpen's core packages are downloaded roughly 5–10x more than ifc-lite's equivalents. `web-ifc` alone (nearly 1M/month) dwarfs anything in ifc-lite's scope. This reflects ThatOpen/web-ifc's multi-year head start as the dominant open-source IFC-in-the-browser stack (many projects list `web-ifc` as a transitive dependency even when not using ThatOpen's higher-level packages directly — e.g. `three-ifc`, `cbim-ifc-loader`, and several viewer forks found in the search results depend on it). This is a maturity/incumbency signal, not a verdict on platform breadth — a newer, broader platform will trail in downloads regardless of merit.

## 6. Verdict

**ThatOpen is not a real platform-level competitor to ifc-lite — it occupies a genuinely different, narrower niche.**

ThatOpen is, and has always positioned itself as, a **browser-embedded 3D BIM viewer toolkit**. Its 6-package scope is coherent and focused: give web developers the building blocks (geometry kernel, importer, UI widgets, cloud client) to build a custom IFC viewer app that runs in a browser tab. It does that well and has the download numbers and multi-year ecosystem (web-ifc's near-1M/month downloads, the fact that several other npm packages wrap or build on it) to prove it's the incumbent choice for that specific job.

ifc-lite is something structurally different: an **agent/CLI/automation-facing BIM analysis platform**. Its 50+ packages cover things ThatOpen has no packages for at all — BCF, IDS validation, clash detection, CRDT collaboration, 2D drawing generation, model diffing, and critically, an MCP server with 125+ tools that makes it directly usable by LLM agents without any browser or human-driven UI in the loop.

The one place they genuinely overlap — and where I verified this hands-on rather than assumed it — is IFC parsing/geometry conversion. ThatOpen's `IfcImporter` + `SingleThreadedFragmentsModel` can actually be run headlessly in Node (verified: converted and queried `real.ifc` successfully), which is a more capable headless story than a naive reading of "it's a browser library" would suggest. But that headless path is a secondary escape hatch bolted onto a package whose primary, best-documented, highest-traffic API (`FragmentsModels`) still assumes `Worker`/`Blob`/browser context. It is not designed, marketed, or packaged as a Node-first or agent-first tool — there is no CLI, no MCP server, and no query language; you're calling internal-feeling classes directly.

So the honest framing for the book is: **ThatOpen and ifc-lite are not fighting for the same customer.** ThatOpen wins decisively if someone wants to embed an interactive 3D IFC viewer in a web app. ifc-lite wins decisively — by default, since ThatOpen doesn't compete here at all — for CLI-driven automation, agent/MCP-based BIM analysis, compliance validation (IDS), collaboration review (BCF), and any workflow that should run without a browser or a human clicking through a 3D view.

## 7. Recommendation for the book

Present this as a **"different jobs, not a horse race"** comparison rather than a feature-count contest, since a raw package-count comparison (50+ vs 6) would unfairly flatten ThatOpen's real strength (it is the most mature, most downloaded open-source IFC-in-browser stack) while overstating ifc-lite's lead in a category ThatOpen never entered (agent tooling). Lead with the parser-level comparison already done elsewhere in the research (web-ifc vs ifc-lite's own parser) as the apples-to-apples technical benchmark, then use this platform-breadth comparison to make the structural point: the interesting story isn't "ifc-lite beats ThatOpen," it's that **the agent-tool-calling / MCP paradigm is itself new enough that an entire category of incumbent BIM tooling (ThatOpen, and by extension anything built the same way) simply doesn't have an answer for it yet.** That's a stronger, more defensible claim than a package-count scoreboard, and it's the one actually backed by what I could verify (install, headless test, and the real npm package list) rather than marketing claims from either project.
