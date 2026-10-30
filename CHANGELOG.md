# Changelog

## 2026-10-30 — book v1.3, 21 rounds of verification complete

- **Book v1.3 ("Final Verified Edition") added** at `book/`.
- **BIMCraft verified hands-on**: cloned, built from source, ran `info`/
  `convert`/`mcp` against the real test building — every cross-checkable
  number matched independently-verified figures exactly; `.rvt`→IFC
  conversion ran ~2.3x faster than rvt-rs's own export.
- **"ifc-lite is the largest Rust BIM project" retired**, checked directly
  via GitHub's language API: 66% TypeScript, 22% Rust, fewer stars (454)
  than BIMCraft (743).
- **openbim-ifc-cli verified**: real, 418K LOC Rust, but young (9 weeks old,
  3 stars) and AGPL/Commercial dual-licensed.
- **Apache Tika's cited prior-art claim corrected**: generic OLE2/CFB
  detection only, no Revit-specific parsing — `rvt-rs`'s own `CLEANROOM.md`
  overstates this.
- **`ifclite-geom` calling convention resolved** and confirmed functional
  (wants raw bytes, not a path string).
- **Full sandbox-escape sweep completed**: dynamic `import('fs')` grants
  arbitrary filesystem read (proven PoC), on top of the earlier
  `process.env`/`fetch` finding. Confirmed, again, that none of this is
  reachable via Claude Desktop's MCP surface — CLI/shell-only.
- Comparisons added this round: `bimcraft-vs-ifclite-rvtrs.md`,
  `openbimifc-vs-ifclite.md`, `tika-vs-rvtrs.md`, `phiag-vs-rvtrs.md`,
  `speckle-vs-rvtrs-ifclite.md`, `bcf-tools.md`, `thatopen-vs-ifclite.md`.
- CSG geometry kernel comparison (`manifold3d`/`opencascade-rs`/`truck`)
  explicitly deferred — lowest priority of the original list, planned as a
  follow-up, not blocking anything above.

## 2026-10-30 — IfcOpenShell / xBim / web-ifc cross-validation

- Independent parallel agents verified ifc-lite/rvt-rs against IfcOpenShell
  (100% agreement across every tested metric) and xBim Essentials (exact
  3-way agreement, perfect round-trip integrity).
- **Critical correction**: the "15-16ms parse" figure was found, independently,
  by two of these agents plus a direct re-test in this session, to have been
  measured on a 24-entity synthetic scaffold file, not the real 970-element
  building. Real figure: ~90-160ms.
- Competitor landscape survey added (6 established Revit-tooling repos).

## 2026-10-30 — initial research push

- Verified `rvt-rs` and `ifc-lite` end-to-end against a real, MIT-licensed
  Revit-authored file (`real.rvt`, 33.7MB, Core Interior project).
- `DEMO_DAY.md` action sheet and `errata-notes.md` research trail created.
- Confirmed: 19 separate `rvt-rs` binaries (not one `rvt` command); MCP
  mutations are in-memory only (CLI `mutate --out` persists; two different
  code paths); CLI `eval` sandbox leaks `process.env`/`fetch`, scoped to
  shell access only, not reachable via MCP.
