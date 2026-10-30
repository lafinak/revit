# Demo Day — single-page action sheet

Everything below is verified today in a Linux devpod. Anything marked
**[UNVERIFIED-WINDOWS]** could not be tested from here and is the real risk
surface for tomorrow — budget troubleshooting time for those specifically.

## 0. Before you leave — 10 minute check on your own laptop

- [ ] Claude Desktop installed, logged in, restarted at least once after any config change
- [ ] Node.js installed; run `npm install -g @ifc-lite/cli` — if it fails with EPERM,
      don't fight it, switch to the npx fallback below
- [ ] Copy `real.ifc` (this folder) onto the demo laptop as the guaranteed fallback file
- [ ] Check Claude Desktop's install type: regular installer vs Microsoft Store (MSIX).
      **[UNVERIFIED-WINDOWS]** MSIX builds may read config from a virtualized path,
      not the one "Edit Config" opens.
- [ ] Disable any other MCP connectors already configured in Desktop for the demo
- [ ] Disable laptop sleep/screensaver for the session

## 1. Claude Desktop config — ready to paste

Config file location:
- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**Preferred** (direct binary, avoids npx pipe issues reported on Windows):
```json
{
  "mcpServers": {
    "ifc-lite": {
      "command": "ifc-lite",
      "args": ["mcp", "C:/path/to/real.ifc"]
    }
  }
}
```
Use forward slashes in the path (`C:/...`), not backslashes — avoids JSON escaping
pitfalls entirely.

**Fallback if the direct binary isn't found on PATH** (npx, with the Windows
cmd-wrapper workaround some users report needing):
```json
{
  "mcpServers": {
    "ifc-lite": {
      "command": "cmd",
      "args": ["/c", "npx", "-y", "@ifc-lite/cli", "mcp", "C:/path/to/real.ifc"]
    }
  }
}
```

**Validate before restarting Desktop**: `python -m json.tool claude_desktop_config.json`
— one syntax error anywhere breaks ALL configured servers, not just this one.

After editing: **fully quit** Claude Desktop (not just close the window), then relaunch.

**[UNVERIFIED-WINDOWS]**: Desktop's actual MCP client behavior (protocol
negotiation, tool-list handling, error recovery) on Windows was never directly
tested — only Claude Code CLI on Linux was. Test this config on your own
Windows-equivalent setup, or at minimum run through step 2 below the moment you
arrive, before anyone's watching.

## 2. First-arrival smoke test (do this before he's even looking)

1. Open Claude Desktop, confirm it shows the `ifc-lite` server as connected
   (Settings → Connectors, or wherever tools are listed)
2. Ask: "How many walls are in the model?" — expect **360** if using the backup
   `real.ifc`, or whatever his real export contains
3. If it doesn't respond or shows "Not connected": **[UNVERIFIED-WINDOWS]** fully
   quit and relaunch Desktop — do not just try to reconnect, multiple user reports
   say that doesn't work
4. Check `%APPDATA%\Claude\logs\` if anything looks wrong and you need to diagnose

## 3. Questions to ask him before trusting his real export

- [ ] Which phase should be exported? (demolished elements never export regardless
      of phase; only one phase per export — this alone can change every count)
- [ ] Does this project have linked Revit models? (excluded from IFC export by
      default unless explicitly enabled)
- [ ] Does he use a lot of in-place/generic-model elements? (these commonly export
      as generic `IfcBuildingElementProxy`, not their real category — causes
      undercounts that look like bugs but aren't)
- [ ] What Revit version? (2024/2025 verified accurate; 2026/2027 experimental,
      2023 untested by us)

## 4. Verified demo script (real numbers, confirmed working right now)

Lead with these, in this order — each one is independently confirmed on the
backup file and safe if his export isn't ready yet:

```
How many walls are in the model?          → 360
How many doors?                           → 132
How many windows?                         → 6
How many spaces?   (NOT "rooms" — see #5) → 116
List all storeys.                         → 15, named Basement 2 through Level 13
List materials used.                      → 9 real wall/floor material types
What's the total floor area?              → 57,737.66 m²
Are there any duplicate GlobalIds?        → "No duplicate GlobalIds found"
What's the largest element in the model?  → a 1,215.45 m² floor slab
```

Nice material-takeoff-style follow-up if things are going well:
```
What door widths exist and how many of each?
→ Expect something like "120 doors at 0.91m, 12 at 0.92m" (verified format, real values will differ on his file)
```

## 5. Known landmines — do NOT improvise around these live

| If you're tempted to ask... | Say this instead | Why |
|---|---|---|
| "How many rooms?" | "How many **spaces**?" | Revit's IFC export uses `IfcSpace`, not `IfcRoom` — "rooms" silently returns 0 |
| "Count all elements" / "how many elements total" | A specific named type, e.g. "how many columns?" | Vague aggregate phrasing maps to the wrong recipe and returns a meaningless number, not an error |
| "What's the window-wall ratio / total wall area?" | "What's the total **floor** area?" | Wall/window area quantity sets are often missing from real exports; floor area reliably works |
| Running `ifc-lite eval` from a shell with a caller-supplied expression | Write the eval string yourself; never pipe his free-text input into one | **CLI `eval` sandbox — critical escalation, treat as equivalent to shell access.** `import('fs').then(fs => fs.readFileSync(path))` **actually read a real file off this machine** — this is arbitrary filesystem read, not just an env-var leak. Static `import ... from` syntax is blocked, but dynamic `import()` is wide open. Also open: `process.env`, `fetch`, `WebSocket`, `Function` constructor, nested `eval()`, `Reflect.construct`, `Proxy`/`Symbol.toPrimitive` tricks, `SharedArrayBuffer`, full `process.argv/cwd/execPath`. Only `require` and `Worker` are confirmed blocked. **Still confirmed not reachable via Claude Desktop MCP** (zero `eval`/`run`/`exec`-named tools in `tools/list`, with or without `--read-only`) — tomorrow's demo is unaffected. But if you ever run `ifc-lite eval` yourself from a terminal, treat it as equivalent to giving the expression full shell-level file access, because it effectively is. |
| `ifc-lite mutate ... --out file.ifc` (CLI, not MCP) | Know this is a *different* code path than MCP mutations | **Persists to disk, unlike MCP mutations.** Confirmed: `mutate --set ... --out mutated.ifc`, then a completely fresh reload of `mutated.ifc`, returned the mutated value. Do not assume "mutations don't persist" applies here — that finding was specifically about MCP's `entity_set_property` via `tools/call`, which is in-memory-only per server process. The CLI `mutate --out` command is a genuinely different, persisting write path. |
| (separate finding) `--read-only` MCP mode | Use for any deployment where the agent shouldn't modify models | **Verified**: hides 40 of 126 MCP tools — the entire mutation surface (`entity_create/delete/set_property/set_attribute`, all `place_*` tools, `edit_hosted_element`, `edit_element_geometry`, `copy_elements`, `duplicate_element`, `array_elements`, `mutation_batch/undo/diff`, `model_save`) plus BCF topic creation, layer publishing, and review-feedback writes. Tool count drops 126 → 86. This is real defense-in-depth for read-only deployments, but it is a **separate control from the eval finding above** — it was never "hiding eval," since eval was never an MCP tool to begin with. |

**If a count looks lower than he expects**: before assuming anything is broken,
check for `IfcBuildingElementProxy` — confirmed today that generic/custom elements
hide there and are invisible to normal "how many X" questions.

## 6. If something breaks — hypothesis order

1. "Claude doesn't see the tools at all" → check config JSON syntax, restart
   Desktop fully, check install type (MSIX vs regular)
2. "Tool call returns empty / no models" → if using HTTP transport, you forgot
   `model_load` — stdio mode doesn't have this problem, prefer stdio
3. "Count looks wrong" → check `IfcBuildingElementProxy`, check which phase was
   exported, check for linked models
4. "It was working, now it's not" → laptop slept, or the MCP server crashed;
   fully quit and relaunch Desktop, don't just reconnect
5. Nothing works at all → fall back to plain CLI: `ifc-lite ask real.ifc "..."`
   with no Claude involved, frame it as "here's the tool directly, here's how an
   agent would call it" — still a legitimate, useful meeting

## 7. If MCP/Desktop integration totally fails

You still have a real demo: the CLI itself, on his real file, answering genuine
questions about his own building, with Claude explaining *why* each number is
what it is. That's not a consolation prize — for an architect, "here's a tool
that reads your Revit file without Revit and answers real questions about it in
under a second" is the actual value proposition, with or without the AI wrapper.

---
Full research trail (6 rounds of testing + 2 rounds of domain research) is in
`errata-notes.md` in this same folder if you need to go deeper on any item above.
