# revit

Research, verification, and demo-prep for a Claude + BIM/Revit toolchain
(`rvt-rs` / `@ifc-lite/cli` / `BIMCraft` / MCP) ahead of a live demo with a
working architect.

Everything in `errata-notes.md` and `comparisons/` was independently verified
in a Linux devpod — and, for the cross-toolchain comparisons, by independent
parallel agents with no shared context — against real, MIT-licensed,
Revit-authored project files. Nothing here is taken on faith from a README.

## Start here

- **[book/](./book/)** — the synthesized narrative (v1.3, "Final Verified
  Edition"), written separately from this research trail. This repo's
  `errata-notes.md` and `comparisons/` are the raw verification evidence
  behind it; read the book for the story, read those for the receipts.
- **[DEMO_DAY.md](./DEMO_DAY.md)** — the single-page action sheet for the
  actual demo day: pre-flight checklist, ready-to-paste Claude Desktop MCP
  config, verified query script, known landmines to avoid live, and a
  fallback plan.
- **[errata-notes.md](./errata-notes.md)** — the full research trail, 21
  rounds: hands-on tool testing, Revit/BIM-domain research,
  Windows/Claude-Desktop platform research, a full sandbox-escape sweep, and
  independent cross-tool verification against IfcOpenShell, xBim, web-ifc,
  BIMCraft, openbim-ifc-cli, Apache Tika, phi-ag/rvt, Speckle, and BCF
  tooling. Go here for the *why* behind any claim in `DEMO_DAY.md` or the book.
- **[comparisons/](./comparisons/)** — nine independent-agent verification
  reports comparing this toolchain against the industry's established tools
  and emerging competitors.
- **[plan.md](./plan.md)** — the original test plan this work executed against.
- **[CHANGELOG.md](./CHANGELOG.md)** — what changed between research/book
  revisions.

## Verified test artifacts

- `real.rvt` — a real Revit-authored file (`2024_Core_Interior.rvt`, MIT license,
  sourced from `magnetar-io/revit-test-datasets`). SHA256-verified byte-exact
  against its Git LFS pointer.
- `real.ifc` — the IFC4 export of `real.rvt` via `rvt-ifc`, 970 real building
  elements with full decoded properties (readiness score 1.00).
- `real-diag.json` — full decode diagnostics for `real.ifc`.
- `einhoven.rvt` / `.ifc` / `-diag.json` — a second real file (Revit 2023,
  different project), used for cross-version validation.
- `demo.rvt` / `diag.json` — a *synthetic* fixture (via `gen-fixture`, no Revit
  involved), kept to document the contrast: synthetic fixtures decode **zero**
  building elements (readiness 0.25), while real files decode fully (1.00).

## Headline findings

**Confirmed as strong, even better than claimed:**
- Every element count claimed for this test file — 360 walls, 132 doors, 6
  windows, 256 columns, 116 spaces — matched real tool output exactly, across
  five independent tools (rvt-rs, ifc-lite, IfcOpenShell, xBim, BIMCraft).
- Independently verified against **IfcOpenShell** (the 11-year-old incumbent):
  **100% agreement** (not the claimed 99.9%) across element counts, spatial
  hierarchy, storey data, floor area, and property-set-level values on 5
  sampled walls (20/20 points exact) — properly scoped to one file, not the
  full claimed corpus.
- Independently verified against **xBim Essentials** (the C#/.NET incumbent):
  exact agreement across all tested element types via a genuine 3-way
  cross-check (xBim / rvt-rs / ifc-lite), perfect round-trip integrity, zero
  duplicate GlobalIds across 17,118 entities.
- Independently verified against **BIMCraft** (see below): every
  cross-checkable number matched exactly, via a completely separate binary
  built from source in this session.

**Corrected, not confirmed:**
- The originally-cited "15-16ms parse" / "~1.2 GB/s tokenization" figures
  were measured on a trivial 24-entity synthetic scaffold file, not the real
  970-element building. **Independently re-measured three separate times**
  (directly in this session, and by two independent agents comparing against
  web-ifc and IfcOpenShell) — the real figure is **~90-160ms / ~32-54 MB/s**.
  Settled, triply-corroborated.
- **"ifc-lite is the largest single Rust BIM project" does not hold.**
  Checked directly via GitHub's own language API for `LTplus-AG/ifc-lite`:
  **66% TypeScript, 22% Rust** — GitHub's primary-language detector reports
  TypeScript, not Rust. ifc-lite also has fewer stars (454) than the project
  below. The claim fails on both language and popularity grounds and should
  be retired, not merely narrowed.
- **`IPedrax/BIMCraft`** (743 stars, Apache-2.0, pure Rust, created just ~2
  weeks before this check) is a full BIM-authoring tool — not just an IFC
  parser — with desktop apps, a real MCP server (verified via handshake: 10
  genuine tools), and its own `.rvt` reader explicitly **"ported in part from
  rvt-rs"** (credited by name in its README). Built from source and run
  against `real.rvt` in this session: every cross-checkable number matched
  exactly what's independently verified elsewhere, and its `.rvt`→IFC
  conversion ran in 2.445s — **~2.3x faster than rvt-rs's own `rvt-ifc`
  export (5.66s)** of the same file.
- `rvt-rs` installs as **19 separate binaries** (`gen-fixture` + 18 `rvt-*`
  tools), not a single `rvt` command.
- Mutations via MCP `tools/call` are in-memory only, never persisting without
  `export_ifc`/`model_save` — but the separate CLI `mutate --out` command
  **does** persist to disk. Two different code paths; don't conflate them.
- **Apache Tika's `.rvt` "support"** (cited as prior art in `rvt-rs`'s own
  `CLEANROOM.md`) is generic OLE2/CFB container detection, not a real Revit
  parser — zero Revit-specific metadata, zero text extraction, same
  classification Tika gives any unrecognized legacy Office binary.
- **`@phi-ag/rvt`** is a real, working, MIT-licensed `.rvt` reader — but it
  only reads container-level metadata and thumbnails, never the internal
  `Partitions/*` streams where the actual building model lives. It doesn't
  refute "only credible reader of the element/schema format," though it does
  mean the book's claim needed that exact qualifier added.
- **`openbim-ifc-cli`** is real (418K LOC of Rust across ~18 crates) but very
  young (created ~9 weeks before this check, 3 stars, AGPL-3.0-or-Commercial
  dual-licensed) — a serious if immature entrant, not a toy.

**Security findings, precisely scoped:**
- The CLI `eval` sandbox provides minimal real isolation: beyond the earlier
  `process.env`/`fetch` finding, a full sweep found **dynamic `import('fs')`
  grants arbitrary filesystem read** (proven — it read a real file off the
  test machine), plus `Function` constructor, nested `eval()`, `WebSocket`,
  and `Reflect.construct` are all reachable. Only `require` and `Worker` are
  confirmed blocked.
- **Critically, this entire surface is CLI/shell-only** — confirmed absent
  from the MCP `tools/list` entirely (no `eval`/`run`/`exec`-named tool
  exists, with or without `--read-only`). Claude Desktop, talking only
  through MCP, cannot reach any of this through ordinary tool-calling.
- `--read-only` MCP mode is real and separately valuable: hides 40 of 126
  tools (the full mutation/create/write surface) — a correct, now-quantified
  defense-in-depth control, just not the fix for the eval finding above.

**Revit-domain findings** (how Revit's own exporter behaves, not tool bugs):
- Only one phase exports at a time; demolished elements never export.
- Linked Revit models are excluded from IFC export by default.
- In-place/generic elements commonly export as generic
  `IfcBuildingElementProxy` — confirmed to cause silent undercounts in
  `ask`-style natural-language queries on this toolchain specifically.

**Competitive landscape** (see `comparisons/competitor-landscape.md`,
`comparisons/speckle-vs-rvtrs-ifclite.md`, `comparisons/bcf-tools.md`,
`comparisons/thatopen-vs-ifclite.md`): no surveyed competitor combines
Revit-independence, a permissive open-source license, and native AI-agent/MCP
tooling at the scale demonstrated here — the closest peer
(`datadrivenconstruction/cad2data`) does the Revit-free trick but is
closed-source and non-commercial-licensed; Speckle and ThatOpen solve
adjacent but genuinely different problems (live collaboration sync, and
browser-embedded viewing, respectively) rather than competing directly.

## What's not yet covered

- **CSG geometry kernel comparison** (`manifold3d`, `opencascade-rs`,
  `truck` vs. ifc-lite's own kernel) — deferred, lowest priority of the
  original research list, planned as a follow-up.
- **Geometry-level fidelity vs. Revit's own native IFC exporter** — requires
  an actual licensed Revit installation, not available from this devpod.

## Provenance

Direct tool testing performed in a Linux devpod (Claude Code). Several of the
reports in `comparisons/` were produced by independent parallel agents with
no shared context with each other or with the main research session — each
installed its own comparison toolchain from scratch and reported findings
without seeing prior claims, which is what allowed them to independently
catch and correct the parse-time discrepancy and the "largest Rust project"
claim's own premise. Platform-specific claims about Windows and Claude
Desktop (as opposed to Claude Code on Linux) are sourced from public bug
reports and documentation, not independently verified — flagged explicitly
wherever they appear.
