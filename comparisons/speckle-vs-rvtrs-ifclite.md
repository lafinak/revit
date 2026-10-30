# Speckle vs. rvt-rs + ifc-lite + MCP

## 1. What Speckle is

Speckle (`specklesystems/speckle-server`, org `specklesystems`) describes itself as "the first AEC data hub that connects with your favorite AEC tools." It is **not** a file-format reader/converter like rvt-rs/ifc-lite — it is a live, server-mediated data synchronization platform for design teams.

**Data model**: graph-based, not IFC/STEP and not Revit-proprietary. Speckle's core abstraction is a dynamic "Base" object with a decomposition API — any connector serializes its native model (Revit elements, Rhino geometry, Grasshopper data, ETABS members, AutoCAD entities, Tekla members, CSi/Civil3D objects) into Speckle's own object graph, which is stored server-side and streamed to a Speckle Server. A threejs-based `@speckle/viewer` package renders that graph in-browser. This is fundamentally a **translation/sync layer between many proprietary tools**, not a neutral open schema like IFC — each connector's converter decides how to map native concepts into Speckle objects, so semantics are connector-specific rather than standardized the way IFC's `IfcWall`/`IfcBeam` classes are.

**Who it's for**: multi-disciplinary AEC teams that need to keep live models in sync across tools — e.g., a Revit model feeding a Grasshopper script feeding an ETABS structural model, with a shared 3D viewer for non-CAD stakeholders. It's a collaboration/interoperability product, not an extraction/analysis product.

**Repo structure** (from the `speckle-server` README, monorepo):
- `packages/server` — Node.js server (the data hub)
- `packages/frontend-2` — Nuxt/Vue web frontend
- `packages/viewer` — threejs 3D viewer (npm package)
- `packages/objectloader` — streams objects from the server API
- `packages/preview-service`, `webhook-service`, `fileimport-service` — supporting services

Connectors live in **separate repos**, current generation in `speckle-sharp-connectors` (.NET): AutoCAD/Civil3D, Rhino, **Revit**, CSi/ETABS, Tekla — plus `specklepy` (Python SDK), and connectors for Sketchup, Excel, Unity, Blender, Unreal, QGIS, PowerBI. The original `speckle-sharp` repo is now explicitly marked **"Legacy"** in its own README, superseded by `speckle-sharp-connectors` + `speckle-sharp-sdk`.

## 2. Real metadata (fetched via GitHub API, 2026-10-30)

| Repo | Stars | Forks | Watchers | Open issues | Language | License | Last push |
|---|---|---|---|---|---|---|---|
| `specklesystems/speckle-server` | 858 | 254 | 858 | 75 | TypeScript | "Other" (Apache-2.0 per README; GitHub license API returns `NOASSERTION`) | 2026-10-29 |

Created 2020-04-14, still actively pushed to daily as of the fetch date — this is a maintained, non-dormant project. I did not separately pull numeric API metadata for `speckle-sharp`/`speckle-sharp-connectors` (only their READMEs), but both are live repos referenced as current by the org.

License note: the README states Apache-2.0 for code, but some modules may carry different licenses (stated explicitly in both `speckle-server` and `speckle-sharp` READMEs) — GitHub's own license detection returned "Other/NOASSERTION," likely because the repo doesn't have a single root `LICENSE` file GitHub's detector trusts fully. Worth a manual check if license terms matter for the book.

## 3. Docker / local quickstart

Docker is available in this environment (`docker --version` → 29.7.2). The `speckle-server` README confirms a local dev path exists: `yarn dev:docker:up` spins up supporting containers (Postgres, Redis, Minio S3, Maildev) alongside `yarn dev` for the Node/Nuxt apps — this is a real, documented local quickstart, not just a hosted-SaaS-only product. I did not actually run it (multi-service Node monorepo bring-up isn't a quick exercise and wasn't the point of this research), but the README's TL;DR (`corepack enable` → `yarn` → `yarn build:public` → `yarn build` → `yarn dev`) and the connector-free server package suggest it's plausible to self-host.

## 4. Architecture comparison

| | **Speckle** | **rvt-rs + ifc-lite + MCP** |
|---|---|---|
| Core function | Live data synchronization hub across many AEC tools | Headless `.rvt` reading + IFC export + agent-queryable BIM data |
| Revit access | **Requires Revit installed** — Revit Connector runs as an in-process Revit add-in (`speckle-sharp-connectors/Connectors/Revit`, targets Revit 2023–2027) | Reads `.rvt` binary files directly in Rust, **no Revit installation needed** |
| Data model | Proprietary graph ("Base" object + decomposition API), connector-specific semantics | IFC/STEP (open standard schema: `IfcWall`, `IfcBeam`, etc.) |
| Server/runtime | Centralized Node.js server + Postgres/Redis/S3, persistent hosted or self-hosted hub | No server required — a library/CLI/MCP toolset operating on files |
| Viewer | Dedicated threejs web viewer (`@speckle/viewer`) for humans | None described — output is structured IFC data for programmatic/agent consumption |
| Multi-tool scope | Revit, Rhino, Grasshopper, AutoCAD/Civil3D, ETABS, Tekla, Sketchup, Excel, Unity, Blender, Unreal, QGIS, PowerBI | Revit (`.rvt`) only, with IFC as the interchange target |
| Primary consumer | Human design teams needing live cross-tool sync + a shared viewer | AI agents and automated pipelines querying/analyzing BIM data (125+ MCP tools) |
| Collaboration model | Real-time push/pull between connectors and server (version-controlled streams) | One-shot/batch extraction and query; no live sync concept |

## 5. MCP / AI-agent tooling

**Confirmed absent.** I grepped both the `speckle-server` and `speckle-sharp` (legacy) READMEs for "mcp" and "agent" — zero matches. Speckle's architecture and public docs predate the Model Context Protocol and show no AI-agent-specific tooling, no MCP server, and no mention of LLM/agent integration in either README. Speckle's "agent" in design-collaboration contexts would mean a human user of a connector, not an AI agent. This is a genuine, confirmable gap relative to the rvt-rs/ifc-lite stack's 125+ MCP tools built specifically for agent-driven querying.

## 6. When would an enterprise choose which?

These solve **different problems** and would often be used by different roles on the same project, not as mutually exclusive choices:

- **Choose Speckle** when the need is live, ongoing data exchange between multiple authoring tools and disciplines — e.g., structural engineers in ETABS need geometry changes from architects in Revit to propagate automatically, or a BIM manager wants a shared web viewer for non-technical stakeholders without exporting files by hand each time. Speckle's value is the *sync and collaboration* layer, and it requires each connected tool (crucially, Revit) to be installed and running to push/pull data.

- **Choose rvt-rs + ifc-lite + MCP** when the need is headless, automatable extraction or analysis of `.rvt` files — e.g., batch-processing thousands of project files in CI without Revit licenses/installations, feeding BIM data into an LLM agent for compliance checking or quantity takeoff, or running on infrastructure where installing Revit per-machine is impractical or impossible (Linux servers, serverless, containers). Its value is *Revit-license-free, agent-native access* to BIM data, not live multi-tool sync.

A BIM team could plausibly use both: Speckle for daily cross-discipline collaboration, and rvt-rs/ifc-lite/MCP for backend automation, QA pipelines, or AI-agent-driven queries that shouldn't require spinning up licensed Revit instances.

## 7. Recommendation for the book

**Yes, mention Speckle — framed as a different category, not a direct competitor.** The clearest framing: Speckle is a *collaboration/interoperability platform* (live sync across authoring tools, requires each tool installed, human-viewer-centric); rvt-rs + ifc-lite + MCP is a *headless extraction/analysis toolkit* (no Revit required, IFC-standard output, agent-native). The single most load-bearing fact for readers is that **Speckle's Revit connector is an add-in that requires a licensed, running Revit instance** — it has no Revit-free reading capability, which is the exact gap rvt-rs fills. A short comparison table (like section 4 above) in a "related tools" or "landscape" section would accurately position both without overstating overlap. Avoid framing this as "Speckle vs. rvt-rs" competition — more accurate is "sync layer vs. extraction layer," and the book should say so explicitly to avoid misleading readers into thinking they're interchangeable.
