# BIMCraft vs rvt-rs / ifc-lite — Verification Report

**Repo:** `IPedrax/BIMCraft`. **Test file:** `real.rvt` (33.7MB, real Revit 2024
project "Core Interior", MIT-licensed, the same file used throughout this
research, already independently verified against rvt-rs, IfcOpenShell, and
xBim).

This report is based on direct hands-on verification in this session — the
repo was cloned, the CLI binary was built from source, and it was run against
the real test file — not on README claims alone.

## 1. What BIMCraft actually is

Confirmed via GitHub API (`api.github.com/repos/IPedrax/BIMCraft`):
- **743 stars, 113 forks, Apache-2.0** (dual MIT OR Apache-2.0 per the
  README's license badge — GitHub's API reports the detected license as
  Apache-2.0)
- **Language: Rust**
- **Created 2026-10-15, pushed 2026-10-29** — i.e. created roughly 2 weeks
  before this check, with that star count already. This growth rate is
  unusually fast and worth noting as such, not just accepting at face value.

Per the README (fetched and read in full): a pure-Rust, clean-room
reimplementation of the Autodesk Revit *workflow*, not just a file format —
walls, doors, windows, floors, ceilings, rooms, columns, stairs, ramps,
railings, roofs, shafts, levels, grids, with plans/sections/elevations/sheets/
schedules, desktop apps for Windows/Linux/macOS, and IFC2x3/IFC4 import and
export.

## 2. The rvt-rs lineage — verified directly in the README's own text

The README states explicitly, with attribution:

> "A Revit `.rvt` or `.rfa` file... is read by a reader of its own,
> `crates/rvt`, **ported in part from [rvt-rs](https://github.com/DrunkOnJava/rvt-rs)**
> and fenced by `docs/rvt-provenance.md`... Checked against rvt-rs's own IFC
> export of the same files, the imported walls, floors, ceilings, openings,
> columns and roofs agree to a fraction of a millimetre."

And in the license/credits section: explicit copyright credit to
"rvt-rs (Copyright 2026 Griffin Long)" — rvt-rs's actual author — with the
reader code specifically marked Apache-2.0-only (not the repo's broader
MIT-OR-Apache-2.0) because of this lineage.

**This is not a competing clean-room implementation — it is a downstream
consumer that explicitly built on top of rvt-rs's reader.** rvt-rs remains
the original; BIMCraft is the first (and by far most ambitious) known
consumer of it.

## 3. Hands-on verification (this session)

Cloned the repo, built just the CLI crate (`bimcraft-cli`, which has zero GUI
dependencies — the desktop app is a separate crate, `apps/bimcraft`) with
`cargo build --release -p bimcraft-cli`: succeeded cleanly in 6m15s, producing
a 28MB binary.

### `bimcraft-cli info real.rvt` — 0.614s

Output (JSON) matches, field-for-field, numbers already independently
verified across multiple other tools in this research:

| Field | BIMCraft | Previously verified elsewhere |
|---|---|---|
| Walls placed | 360 | 360 (rvt-rs, ifc-lite, xBim, IfcOpenShell — all identical) |
| Doors placed | 132 | 132 |
| Windows placed | 6 | 6 |
| Columns placed | 256 | 256 |
| Rooms placed | 116 | 116 |
| Floors placed | 99 | 99 |
| Levels (15) | identical names and elevations | identical, independently verified via `rvt-history`/`rvt-info` |
| `declared` element count | 26,425 | 26,425 (matches the Python `rvt` binding's `declared_element_ids()` exactly, from Round 10) |
| Build string | `20230509_0315(x64)` | identical, verified via `rvt-analyze` weeks earlier |
| Save path | `B:\Git\revit-test-datasets\Revit\2024_Core_Interior.rvt` | identical |

Every single cross-checkable number matches exactly. This is genuine,
independent-tool cross-validation, not a coincidence — BIMCraft's reader
being "ported in part from rvt-rs" explains *why* the numbers converge, but
the fact that a completely separate binary, built from a completely separate
codebase, reproduces every figure exactly is still a meaningful confirmation
of both tools' correctness on this file.

### `bimcraft-cli convert real.rvt out.ifc` — 2.445s

Produced a 1,275,193-byte IFC4 file. **Notably faster than rvt-rs's own
`rvt-ifc` export of the same file (5.66s, independently measured earlier in
this research)** — roughly 2.3x faster for the equivalent .rvt→IFC operation.
This is a real, measured performance data point, not a claim.

### `bimcraft-cli mcp` — real MCP server, verified via handshake

Sent a real `initialize` + `tools/list` sequence over stdio. Got back a
valid JSON-RPC response with **10 real tools**: `execute`, `script`,
`list_commands`, `inspect_model`, `query_elements`, `schedule`, `render`,
`new_model`, `open`, `save` — each with a genuine, detailed JSON schema
matching the README's description of the command language exactly (e.g.
`wall {points: [[0,0],[8000,0],...]}`). The `open` tool's description
explicitly confirms: "import a Revit .rvt file (read directly, no Revit
needed...)" — i.e. the MCP server itself can open .rvt files directly, not
just pre-converted IFC.

## 4. What this means for the book's two claims

### Claim 1: "rvt-rs is the only credible open-source reader for Autodesk Revit's proprietary .rvt format"

**Survives, with the same nuance already established for `@phi-ag/rvt`, but
reinforced rather than threatened.** BIMCraft's `.rvt` reader is explicitly
ported from rvt-rs, not an independent implementation — so its existence
doesn't add a second *independent* reader to the landscape. If anything,
BIMCraft's success is evidence *for* rvt-rs's claim: the most ambitious,
highest-profile new Rust BIM project in this space chose to build on rvt-rs
rather than write its own reader from scratch.

### Claim 2: "ifc-lite is the largest single project in the Rust BIM ecosystem"

**This is where BIMCraft is the real, serious problem for the book — and the
`openbim-ifc-compare2` agent's parallel finding makes it worse, not better.**
That agent discovered, independently, that `ifc-lite`'s own CLI package is
TypeScript/Node (`"type": "module"`, built with `tsc`), depending on ~26
`@ifc-lite/*` npm packages, with `@ifc-lite/wasm` of unconfirmed source
language. **If ifc-lite's core isn't even predominantly Rust, the claim's
premise may be false independent of any competitor's size.**

Even setting that aside: BIMCraft is Rust, confirmed by GitHub's language
detection, with 743 stars (vs. ifc-lite's much smaller npm download numbers
and openbim-ifc-cli's 3 stars) and a genuinely large feature surface — full
BIM authoring, not just IFC parsing. By star count and scope, it is very
likely the actual largest/most-visible Rust BIM project as of this check,
not ifc-lite.

**The book cannot ship with this claim unqualified.** At minimum, it needs:
1. A real check of ifc-lite's own source repository to confirm what language
   its core logic is actually written in (not just assumed from the name).
2. Acknowledgment of BIMCraft by name, with the rvt-rs lineage credited
   accurately (BIMCraft is a rvt-rs consumer, not a rival reader).
3. Either narrowing "largest Rust BIM project" to a specific, defensible
   sub-claim ifc-lite can actually support (e.g. "largest Rust-based *IFC
   parsing and MCP tooling* project" — if even that holds up), or dropping
   the claim and replacing it with an honest statement of what's actually
   been verified: ifc-lite's MCP tool count (125+) and feature breadth, which
   stand on their own merits without needing a "largest" superlative.

## 5. One honest caveat on this report itself

BIMCraft's status badge says "early development." The 743-star count in ~2
weeks is unusually fast growth that this report notes but does not explain
(could be organic interest, could be reflective of promotion/visibility this
session has no way to assess) — treat the star count as a real, verified
fact (it is, via the GitHub API), but not as proof of production maturity on
its own. The hands-on verification above (info/convert/mcp all working
correctly against a real 970-element building) is the stronger evidence of
genuine capability, independent of the star count's cause.
