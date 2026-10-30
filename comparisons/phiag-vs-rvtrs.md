# `@phi-ag/rvt` vs `rvt-rs` — does phi-ag/rvt refute "the only credible open-source reader"?

Test file: `/workspaces/turbo-flow-wsl/dev/architektura/revitest/real.rvt` (33.7 MB, Revit 2024, "2024_Core_Interior", MIT-licensed test dataset).
Date: 2026-10-30.

## 1. Install result

```
mkdir -p /tmp/phiag-test && cd /tmp/phiag-test && npm init -y && npm install @phi-ag/rvt
```

Installed cleanly: **1 package added, 0 vulnerabilities**.

- Version: **0.3.0**
- License: MIT
- Installed footprint: **144 KB** (`node_modules/@phi-ag`) — this is a genuinely small, dependency-free package (no other packages were pulled in).
- Package type: ESM-only (`"type": "module"`), with subpath exports `.` (browser-safe `index.js`), `./node` (adds `openPath` using `fs`), `./deno`.

## 2. Verbatim output

### `@phi-ag/rvt` test script (`openPath` → `basicFileInfo` → `thumbnail` → `entries()`)

```
openPath: 7.05 ms
basicFileInfo: 1.08 ms
basicFileInfo result: {
  "fileVersion": 14,
  "version": "2024",
  "build": "20230509_0315(x64)",
  "path": "B:\\Git\\revit-test-datasets\\Revit\\2024_Core_Interior.rvt",
  "locale": "ENU",
  "identityId": "00000000-0000-0000-0000-000000000000",
  "documentId": "2a619b2e-a277-4154-90ff-ca7b37baec5b",
  "appName": "Autodesk Revit",
  "content": "Worksharing: Not enabled\r\nUsername: \r\nCentral Model Path: \r\nFormat: 2024\r\nBuild: 20230509_0315(x64)\r\nLast Save Path: B:\\Git\\revit-test-datasets\\Revit\\2024_Core_Interior.rvt\r\n...Unique Document GUID: 2a619b2e-a277-4154-90ff-ca7b37baec5b\r\n...IsSingleUserCloudModel: 慆獬e\r\nAuthor: Autodesk Revit\r\nClientAppName: RevitApplication"
}
thumbnail: 1.43 ms
thumbnail blob type: image/png size: 9544
entries(): 0.02 ms, total count: 24
```

First 20 entries (CFB directory records — names/paths only, abbreviated fields shown):
```
Root Entry (storage)
Formats (storage)
RevitPreview4.0 (stream, 9886 bytes)
Global (storage)
Partitions (storage)
Contents (stream, 276 bytes)
TransmissionData (stream, 1946 bytes)
BasicFileInfo (stream, 2107 bytes)
ProjectInformation (stream, 764 bytes)
Partitions/46 (stream, 17,072,209 bytes)   <- the real element partition
Global/DocumentIncrementTable (stream, 1967 bytes)
Global/History (stream, 837 bytes)
Global/PartitionTable (stream, 134 bytes)
Global/ContentDocuments (stream, 243,084 bytes)
Global/ElemTable (stream, 125,892 bytes)
Global/Latest (stream, 78,810 bytes)
Formats/Latest (stream, 173,230 bytes)
Partitions/48 (stream, 2,388,625 bytes)
Partitions/51 (stream, 598,771 bytes)
Partitions/55 (stream, 2,695,935 bytes)
```

Entries matching `global|format|basicfile|partatom` (case-insensitive): **4 matches** — `Formats`, `Global`, `BasicFileInfo`, `ProjectInformation`. (Note: the filter string had a typo carried over from the brief — "partatom" doesn't exist in this file; the actual element-bearing streams are named `Partitions/NN`, which the regex as given does not catch. Re-running with `partition` instead of `partatom` additionally matches all `Partitions/*` entries, confirming phi-ag/rvt *sees* the partition streams — it just doesn't parse what's inside them.)

### `rvt-rs` (`rvt-info`, no flags)

```
Revit file · real.rvt
  version:       2024
  build:         20230509_0315(x64)
  locale:        ENU
  file GUID:     2a619b2e-a277-4154-90ff-ca7b37baec5b
  original path: B:\Git\revit-test-datasets\Revit\2024_Core_Interior.rvt
  partition:     Partitions/46
  streams:       20 (33589540 total bytes)

Document ·
  title:          2024_Core_Interior
  last saved:     2023-09-07 12:50:35 UTC
  worksharing:    Not enabled
  save counter:   66
  cloud model:    no

Schema ·
  class names (inferred): 8575

real    0m0.050s
```

### `rvt-rs` (`rvt-info --show-classes`)

Same header, plus a sample of inferred schema class names (8,575 total): `A3PartyAImage`, `A3PartyObject`, `ADocument`, `AProperty`, `APropertyDouble1` … (full list truncated here; command took 0.034s).

## 3. Comparison table

| Feature | `rvt-rs` | `@phi-ag/rvt` |
|---|---|---|
| Open/parse CFB container | ✅ | ✅ |
| File version / build / GUID / original path | ✅ | ✅ (identical values recovered) |
| Worksharing / save-counter / locale | ✅ | ✅ (inside the raw `content` text block; not individually parsed fields, just the same text Revit itself writes) |
| List raw CFB streams/storages | ✅ (`streams: 20`) | ✅ (`entries(): 24` — includes storage *and* stream nodes, hence the higher count) |
| Thumbnail/preview image extraction | not in the tested commands (not advertised as a differentiator here) | ✅ — decodes `RevitPreview4.0` into a PNG `Blob` in ~1.4ms |
| **Schema/class name enumeration** (8,575 inferred class names) | ✅ | ❌ — no API surface for this at all |
| **Element decoding** (walking `Partitions/NN` packed binary element streams into structured data) | ✅ (dedicated pipeline; this is `rvt-rs`'s core differentiator, used by `rvt-elements`, `rvt-ifc`) | ❌ — `Partitions/*` are visible as raw opaque streams only; nothing in the public API decodes their contents |
| IFC export | ✅ (`rvt-ifc`) | ❌ |
| Runtime | Native Rust binary / library, WASM build exists but unverified published status (see §6) | Pure TypeScript — runs unmodified in Node, Deno, and browser (no WASM needed) |
| Dependencies | n/a (native binary) | zero npm dependencies, 144 KB installed |
| License | (not re-verified here; assumed from prior session) | MIT |

## 4. Performance comparison

| Operation | `rvt-rs` | `@phi-ag/rvt` |
|---|---|---|
| Open + basic metadata | `rvt-info` end-to-end: ~34–50ms (process startup included) | `openPath`: 7.05ms, `basicFileInfo`: 1.08ms (in-process, no startup cost) |
| Schema/class enumeration | included in the ~34–50ms above | not applicable — feature doesn't exist |
| Thumbnail | not measured in this comparison | 1.43ms |

Both are fast. `rvt-rs`'s number includes OS process spawn; `@phi-ag/rvt`'s is pure in-process JS timing, so these aren't perfectly apples-to-apples, but neither tool is anywhere near a bottleneck for metadata-level work on a 33.7MB file.

## 5. Strategic verdict

**`@phi-ag/rvt` is a real, working, MIT-licensed library that correctly parses the Revit CFB container and extracts `BasicFileInfo` and the embedded preview thumbnail. It is credible at what it does.** The install was clean, the output was verified against the same ground-truth file already validated against `rvt-rs`, and the extracted version/build/GUID/path/worksharing data matched exactly.

**However, it is not a competing alternative to `rvt-rs` for the book's apparent scope, and it does not refute "the only credible open-source reader" claim as that claim is actually about element decoding.** The decisive evidence is `rvt-info --show-classes`: `rvt-rs` enumerates **8,575 inferred schema class names** and has a dedicated pipeline (feeding `rvt-elements`, `rvt-ifc`) that walks the packed binary `Partitions/NN` streams and decodes them into structured building elements. `@phi-ag/rvt`'s public API — `basicFileInfo`, `thumbnail`, `entries`, `openPath` — has **no function that touches the contents of the `Partitions/*` streams at all**. Its `Cfb.entries()`/`entryData()` only exposes the CFB directory structure and raw bytes; nothing in `dist/` parses Revit's internal element schema. This is the difference between "can open a .rvt file and read its header" and "can read a .rvt file's building model."

So the honest framing is:
- Both tools **can open .rvt files and read file-level metadata** (version, build, GUID, worksharing state, path). On this narrow slice, they're roughly equivalent, and `@phi-ag/rvt` adds thumbnail extraction, which wasn't tested against `rvt-rs` here.
- Only `rvt-rs` **decodes the proprietary internal element format** — the actual "reader" capability that a claim about ".rvt format reading" would reasonably be understood to mean to a BIM/AEC audience (walls, floors, families, parameters, geometry).
- Treating "`@phi-ag/rvt` exists and reads .rvt files" as refuting "only credible reader of the .rvt format" conflates **container-level metadata extraction** with **full model/element extraction**. They are materially different capabilities aimed at different use cases (file-picker previews/validation vs. actual BIM data extraction/interop).

## 6. Recommendation for the book

Do not drop the uniqueness claim, but **narrow and sharpen it** rather than leaving it as an unqualified "only credible reader":

1. Reframe the claim from "the only credible open-source reader for .rvt" to something like: **"the only open-source tool that decodes Revit's internal element/schema format into structured building data — as opposed to the handful of tools (e.g. `@phi-ag/rvt`) that parse the outer CFB container for file metadata and thumbnails only."** This is both more defensible and more informative to readers.
2. Add a short "prior art" sidebar in the book acknowledging `@phi-ag/rvt` by name — crediting it for the metadata/thumbnail use case (it's genuinely good at this, zero-dependency, cross-runtime) while explicitly contrasting it with `rvt-rs`'s element-decoding scope. This pre-empts exactly the "wait, isn't X already open-source?" challenge a technical reader will raise, and strengthens rather than weakens the book's credibility.
3. If the book wants to keep a strong one-line claim, use: **"rvt-rs is, to our knowledge, the only open-source tool that decodes Revit's proprietary element/geometry data — not just its file header."** Avoid "only credible reader" as a blanket phrase since "reader" is ambiguous between header-reading and model-reading, and `@phi-ag/rvt` is a legitimate (if narrower) open-source header/thumbnail reader with modest but real adoption (~4,193 downloads/month, ~1,048/week per npm's download API as of 2026-10-28 — small, but not zero, and growing interest in this space is itself worth a footnote).
4. Note the WASM angle only lightly: `rvt-rs` apparently has a `rvt-wasm` crate/package for browser use, but within the 2-minute budget I could not confirm it's published — `npm view rvt-wasm` returned a 404 on the public npm registry, and `crates.io` was unreachable from this sandbox (empty response, likely network-restricted here, not necessarily down). **This is unverified, not confirmed-absent** — the book should not claim `rvt-wasm` is published without checking from an environment with full internet access, and should not imply equivalence with `@phi-ag/rvt`'s native, dependency-free browser support either way until that's resolved.

## Honesty notes on what wasn't fully tested

- The `partatom` term in the requested grep had no matches in this file (likely a brief typo) — I re-ran with `partition` to confirm phi-ag/rvt does enumerate the `Partitions/*` streams; it does, but doesn't parse their contents.
- `rvt-wasm` publish status is **inconclusive**, not negative — crates.io did not respond in this sandbox (possibly a network egress restriction), and this was within the 2-minute cap set for that sub-point.
- Download stats reflect npm's public API as queried 2026-10-30, for the week ending 2026-10-28 and month ending 2026-10-28; this is a point-in-time signal, not a trend.
