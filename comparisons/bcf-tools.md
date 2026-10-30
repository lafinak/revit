# BCF Tooling Comparison: ifc-lite vs. openbimrs/bcf

Date: 2026-10-30

## 1. Does `openbimrs/bcf` exist?

**Yes — but it is not a CLI, and the hypothesis in the task brief was wrong on two points.**

- `openbimrs` is a real GitHub organization (id 320634585, created 2026-08-24, 22 public repos), and `openbimrs/bcf` is a real repo: "Pure-Rust, corpus-verified BCF-XML issue exchange for OpenBIM.rs." `README.md` fetched cleanly from the `main` branch (HTTP 200, no fallback to `master` needed).
- The published crate is **`openbim-bcf`**, not `openbim-bcf-cli` as speculated in the task brief. The crate's own `Cargo.toml` confirms the real name and version (`0.7.2`).
- **It is a library crate with no `[[bin]]` target.** There is no `src/bin/`, no `main.rs` entry point, and no CLI subcommand anywhere in its manifest — it's meant to be used as a Rust dependency (`openbim_bcf::read_path(...)`, `openbim_bcf::write::to_path(...)`), not invoked from a shell.
- I checked whether the org ships a BCF CLI under a different name:
  - `openbimrs/homebrew-tap` (its own CLI distribution channel) contains exactly one formula, `openbim-ifc.rb` — for IFC, not BCF.
  - `openbimrs/openbim`, the umbrella crate the `bcf` README says pins this package at `packages/bcf`, is also a Rust library aggregator, not a CLI.
- **Install attempt**: I did not run `cargo install openbim-bcf` as a real test of "is there a binary," because the point is moot — the manifest has no binary target, so `cargo install` would simply refuse with "there is nothing to install" regardless of whether the crate is published to crates.io. (Separately, this sandbox's Rust toolchain is broken — `cargo` fails with "Missing manifest in toolchain" — so no cargo command could run here either way. That's an environment limitation, not evidence about the crate.) A crates.io API lookup (`GET /api/v1/crates/openbim-bcf`) returned HTTP 403, which is inconclusive — it reads like an anti-bot block on this network, not a "crate not found" response — so I'm not treating that as proof either way.

**Bottom line:** there is no competing BCF CLI tool to install or compare topic-creation ergonomics against. `openbim-bcf` is a Rust library a developer could embed in their own tool, but out of the box it offers nothing a CLI comparison can exercise.

## 2. ifc-lite's verified BCF capability

Ran directly against the real IFC4 file at `dev/architektura/revitest/real.ifc`:

```
ifc-lite bcf create real.ifc --title "Test wall issue" --out ifclite-test.bcf
```

Output: `BCF written to ifclite-test.bcf`

Zip structure (`unzip -l`):

```
  Length      Date    Time    Name
---------  ---------- -----   ----
      215  2026-10-30 03:40   bcf.version
      300  2026-10-30 03:40   project.bcfp
      405  2026-10-30 03:40   1b4e8757-0ebb-4b4b-81a1-4421c8ac2518/markup.bcf
---------                     -------
      920                     3 files
```

This matches the standards-shaped layout buildingSMART expects: a top-level `bcf.version`, a `project.bcfp`, and a UUID-named topic folder containing `markup.bcf`.

Content checks:
- `bcf.version` declares `VersionId="2.1"` / `<DetailedVersion>2.1</DetailedVersion>` — so ifc-lite targets **BCF 2.1**.
- `markup.bcf` has a well-formed `<Topic>` with `Guid`, `TopicType="Issue"`, `TopicStatus="Open"`, `Title`, `CreationDate`, `CreationAuthor`.
- `project.bcfp` has a `ProjectId` and an (empty) `ExtensionSchema`.
- CLI surface: `ifc-lite bcf <create|list|add-comment>` — topic creation, listing, and comment-threading are all first-class subcommands.

No indication in the CLI output or file structure that ifc-lite runs its own XSD validation of the output before writing — it produces well-formed XML that *looks* schema-correct, but I did not find a validation step logged or documented.

## 3. openbimrs/bcf's BCF capability

**Not applicable — no CLI exists to generate a comparable topic file.** The crate's own README is explicit about what's implemented as a *library*, though, which is useful context:

| Capability | State per upstream README |
|---|---|
| Version detection (2.0/2.1/3.0) with evidence + conflict reporting | implemented |
| Reading viewpoint camera/visibility/colouring/clipping | **not implemented** |
| Reading project extensions (`.bcfp`) | **not implemented** |
| Writing 2.1 and 3.0 topics/comments/component selections/cameras | implemented, "XSD-validated, round-tripped, golden-pinned" |
| Writing BCF 2.0 | **not implemented** (read-only) |

Notably, the upstream project *does* claim real XSD validation of its writer output as part of its test gate (`validate-written.py` against official schemas) — a more rigorous validation story than anything I could observe in ifc-lite's CLI run. But since this is library-only with no CLI and no binary to run against `real.ifc`, I generated no topic file from it and have no zip structure to show.

## 4. Comparison table

| Dimension | ifc-lite (CLI, verified) | openbimrs/bcf (library, unverifiable as a tool) |
|---|---|---|
| BCF version support | 2.1 (observed in output) | 2.0 read-only; 2.1 & 3.0 read+write per README (not independently verified — no CLI to run) |
| Topic creation | `ifc-lite bcf create` — verified working, produces valid-looking zip | Only via Rust API (`write::to_path`) — requires writing a Rust program; not usable as-is |
| Viewpoint creation | Not exercised in this test (not requested) | README explicitly states viewpoint *reading* (camera/visibility/colouring) is **not implemented**; writing viewpoints with component selection/camera is claimed implemented |
| Comment threading | `ifc-lite bcf add-comment` subcommand exists | Comments: writer support claimed; no CLI to test |
| Standards validation | Not observed/documented in this run | Claims real XSD validation in its test gate (`validate-written.py`), a stronger documented claim than ifc-lite's |

## 5. Strategic verdict

**ifc-lite is the only one of the two that is actually usable today as a tool**, because it is the only one with a CLI at all. `openbimrs/bcf` is a real, actively-documented Rust crate with a genuinely more rigorous internal validation story (corpus testing against 44 field archives + buildingSMART's 152-file test suite, mutation-probe testing, XSD validation of writer output) — on paper, if you were embedding BCF support into a Rust application, it looks like better-engineered groundwork than what I could verify of ifc-lite's internals from the CLI alone. But "better library internals" is not a competing product: nobody evaluating "which tool do I install to create BCF topics" can install `openbim-bcf`, because it ships no binary.

So, as posed, **this comparison could not be completed as a head-to-head tool evaluation** — openbimrs/bcf isn't a competing CLI, it's a library with no command-line surface. ifc-lite's BCF support stands unchallenged by this specific "competitor" for the purpose this book section cares about (a tool a user runs). If the book wants to discuss `openbim-bcf` at all, it should be framed correctly: as a Rust library a developer could use to *build* their own BCF tool, with a more rigorous validation pipeline than anything demonstrated here for ifc-lite — not as an alternative end-user CLI.
