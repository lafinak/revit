# revit

Research, verification, and demo-prep for a Claude + BIM/Revit toolchain
(`rvt-rs` / `@ifc-lite/cli` / MCP) ahead of a live demo with a working architect.

Everything here was independently verified in a Linux devpod against a real,
MIT-licensed, Revit-authored project file — not taken on faith from READMEs.

## Start here

- **[DEMO_DAY.md](./DEMO_DAY.md)** — the single-page action sheet for the actual
  demo day: pre-flight checklist, ready-to-paste Claude Desktop MCP config,
  verified query script, known landmines to avoid live, and a fallback plan.
- **[errata-notes.md](./errata-notes.md)** — the full research trail: six rounds
  of hands-on tool testing plus two rounds of Revit/BIM-domain and
  Windows/Claude-Desktop-platform research. Go here for the *why* behind any
  claim in DEMO_DAY.md.
- **[plan.md](./plan.md)** — the original test plan this work executed against.

## Verified test artifacts

- `real.rvt` — a real Revit-authored file (`2024_Core_Interior.rvt`, MIT license,
  sourced from `magnetar-io/revit-test-datasets`). SHA256-verified byte-exact
  against its Git LFS pointer.
- `real.ifc` — the IFC4 export of `real.rvt` via `rvt-ifc`, 970 real building
  elements with full decoded properties (readiness score 1.00).
- `real-diag.json` — full decode diagnostics for `real.ifc` (exact-geometry vs.
  bounding-box-only element breakdown, confidence scores, unit recovery).
- `demo.rvt` / `diag.json` — a *synthetic* fixture (via `gen-fixture`, no Revit
  involved) and its diagnostics, kept specifically to document the contrast:
  synthetic fixtures exercise only the container/metadata layer and decode
  **zero** building elements (readiness score 0.25, "scaffold-only"), while
  `real.rvt` decodes the full building (readiness score 1.00). This gap is one
  of the key corrections to the source material's claims.

## Headline findings (see errata-notes.md for full detail)

- Every element count the source material claimed for this exact test file —
  360 walls, 132 doors, 6 windows, 256 columns, 116 rooms — matched real tool
  output exactly.
- `rvt-rs` (the Rust Revit reader) installs as **19 separate binaries**
  (`gen-fixture` + 18 `rvt-*` tools), not a single `rvt` command.
- The `@ifc-lite/cli` MCP server exposes **125+ real tools** over both stdio and
  HTTP transport, confirmed working end-to-end with `claude mcp add`.
- Mutations via MCP are in-memory only per server process — never persist
  without an explicit `export_ifc`/`model_save` call, confirmed by direct test.
- The `eval` sandbox blocks `require`/`XMLHttpRequest` but **not** `process.env`
  or `fetch` — a real (if narrow) exfiltration primitive, worth flagging in any
  security-relevant documentation.
- Revit's own IFC exporter has real, documented quirks that affect any tool
  built on top of it: only one phase exports at a time (demolished elements
  never export), linked models are excluded by default, and in-place/generic
  elements commonly export as generic `IfcBuildingElementProxy` — confirmed to
  cause silent undercounts in `ask`-style natural-language queries.

## Provenance

All testing performed in a Linux devpod (Claude Code). Platform-specific claims
about Windows and Claude Desktop (as opposed to Claude Code on Linux) are
sourced from public bug reports and documentation, not independently verified —
this is flagged explicitly wherever it applies in `errata-notes.md` and
`DEMO_DAY.md`.
