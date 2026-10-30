Jasné. Tu je kompletný master checklist na dnešok — všetko čo treba otestovať v tvojom devpode s Claude Code. Štruktúrované ako master task, ktorý môžeš hodiť priamo Claude Code ako jeden veľký prompt alebo rozdeliť na menšie.

---

# Master Checklist — Devpod Testing (dnes večer)

## Setup overenia (urob prvé, ak nie sú)

```bash
source $HOME/.cargo/env
which ifc-lite rvt-info gen-fixture claude python3
ifc-lite --version
rvt-info --version 2>&1 | head -3
gen-fixture --version 2>&1 | head -3
claude --version
```

Ak čokoľvek chýba, doinštaluj:
- `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && source $HOME/.cargo/env && cargo install rvt --locked`
- `npm install -g @ifc-lite/cli`
- `pip install rvt`

---

## Fáza 1: Reálny .rvt súbor (KRITICKÉ)

Bez neho Pattern D neotestuješ. Toto je najdôležitejšia vec na dnešok.

### 1.1 Získať reálny .rvt
```bash
# Skús každý zdroj postupne
mkdir -p /tmp/rvt-tests && cd /tmp/rvt-tests

# Zdroj A: magnetar-io (používa rvt-rs na validáciu)
git clone https://github.com/magnetar-io/revit-test-datasets .
ls -lh *.rvt 2>&1

# Zdroj B: ak A zlyhá, skús Autodesk sample súbory
# (často redistributable, over EULA)
# https://knowledge.autodesk.com/customer-service/download-install/download-sample-files

# Zdroj C: puzzbobb's R2025 models
git clone https://github.com/puzzbobb/revit-test-datasets puzzbobb 2>&1 | tail -3

# Zdroj D: BIM4LCA
git clone https://github.com/BIM4LCA/office bim4lca 2>&1 | tail -3
```

Ak sa ti podarí získať aspoň jeden .rvt súbor, ulož ho ako `/tmp/real.rvt`.

### 1.2 Ak zlyhá všetko — prepis na "Pattern D limitation demo"

Ak reálny .rvt nedáš, Pattern D na tomorrow sa obmedzí na inšpekciu metadát + IFC z Revitu exportovaného. To je stále legit demonštrácia, ale menej pôsobivá.

---

## Fáza 2: Pattern D — rvt-rs na reálnom .rvt (ak máš)

```bash
# Verifikácia clean-room reader
time rvt-info /tmp/real.rvt --show-classes > /tmp/rvt-info.out 2>&1
time rvt-elements /tmp/real.rvt --counts > /tmp/rvt-elements.out 2>&1
time rvt-ifc /tmp/real.rvt -o /tmp/real.ifc --diagnostics /tmp/diag.json > /tmp/rvt-ifc.out 2>&1
ls -lh /tmp/real.ifc /tmp/diag.json
cat /tmp/diag.json > /tmp/diag.out

# Vygeneruj aj glTF + SVG
time rvt-gltf /tmp/real.rvt -o /tmp/real.glb
time rvt-sheet /tmp/real.rvt -o /tmp/real.svg
ls -lh /tmp/real.glb /tmp/real.svg

# Python binding tiež
python3 -c "
import rvt, json
f = rvt.RevitFile('/tmp/real.rvt')
print('version:', f.version)
print('build:', f.build)
print('original_path:', f.original_path)
print('schema_summary:', f.schema_summary())
print('element_counts:', f.element_counts())
"
```

**Zaznamenaj**: reálne element counts vs. knižné tvrdenia, latencie, diagnostic accuracy (exact vs bounding-box).

---

## Fáza 3: Pattern D — rvt-rs na syntetickej fixture (overenie limitu)

```bash
# Overenie, čo syntetická fixture dokáže a nedokáže
gen-fixture demo --classes Wall,Level,Project,Column,Door --element-count 25 --year 2024 --output /tmp/demo.rvt
rvt-info /tmp/demo.rvt
rvt-elements /tmp/demo.rvt --counts   # očakávaj total: 0 (limit)
rvt-ifc /tmp/demo.rvt -o /tmp/demo.ifc --diagnostics /tmp/demo.diag.json
cat /tmp/demo.diag.json | head -20    # očakávaj "scaffold-only", readiness 0.25

ifc-lite info /tmp/demo.ifc --json    # over že ifc-lite parse prejde
```

**Zaznamenaj**: presne aké vrstvy fungujú (container, schema) a aké nie (elements, geometry). Toto bude Errata section v knihe.

---

## Fáza 4: Pattern E — ifc-lite CLI exhaustive test

Toto je najdôležitejšia časť na tomorrow. Prejdeme každý subcommand.

### 4.1 Setup test files
```bash
# Hlavný test IFC súbor — vytvor väčší model s viacerými typmi
ifc-lite create wall --start 0,0,0 --end 5,0,0 --height 3 --thickness 0.2 --out /tmp/w1.ifc
ifc-lite create wall --start 5,0,0 --end 10,0,0 --height 3 --thickness 0.2 --out /tmp/w2.ifc
ifc-lite create wall --start 10,0,0 --end 15,0,0 --height 3.5 --thickness 0.2 --out /tmp/w3.ifc
ifc-lite merge /tmp/w1.ifc /tmp/w2.ifc /tmp/w3.ifc --out /tmp/multi.ifc
ifc-lite info /tmp/multi.ifc --json

# Ak máš reálny .rvt z Fázy 1, použi aj ten
if [ -f /tmp/real.ifc ]; then
  cp /tmp/real.ifc /tmp/multi.ifc   # reálny dátový súbor
fi
```

### 4.2 Full --help (zachytiť všetko, žiadne slice)
```bash
ifc-lite --help > /tmp/help-main.txt
wc -l /tmp/help-main.txt
cat /tmp/help-main.txt
```

### 4.3 Každý subcommand systematiky
Pre každý z 30 subcommands (info, query, props, export, schedule, diagnose-geometry, extract-entities, anonymize, ids, bcf, clash, create, eval, run, schema, merge, convert, diff, rekey, validate, bsdd, stats, analyze, lod, doctor, mutate, generate-spaces, ask, view, mcp):

```bash
# Pre každý SUBCOMMAND:
SUB=<subcommand>
ifc-lite $SUB --help > /tmp/help-$SUB.txt 2>&1
echo "=== $SUB --help ===" 
cat /tmp/help-$SUB.txt | head -40
echo ""
echo "=== $SUB test run ==="
ifc-lite $SUB /tmp/multi.ifc 2>&1 | head -30   # uprav args podľa help
echo ""
echo "=== $SUB exit code: $? ==="
```

(Namiesto ručného opakovania spusti ako bash loop.)

### 4.4 `ask` recipe set (kritické pre tomorrow)
```bash
# Capture all ask recipes
ifc-lite ask --help > /tmp/help-ask.txt 2>&1
cat /tmp/help-ask.txt   # FULL, no slice

# Test each candidate recipe phrase
for q in "how many walls?" "how many doors?" "how many windows?" \
         "list all rooms" "exterior walls" "load-bearing walls" \
         "fire rated doors" "window-wall ratio" "count rooms" \
         "list storeys" "spatial hierarchy" "material quantities" \
         "orphaned elements" "duplicate types"; do
  echo ">>> ask '$q'"
  ifc-lite ask /tmp/multi.ifc "$q" 2>&1
  echo "---"
done
```

### 4.5 `eval` bim.* API surface (komplexné LLM-style queries)
```bash
# Plný SDK schema
ifc-lite schema > /tmp/schema.json
wc -l /tmp/schema.json
python3 -c "import json; d=json.load(open('/tmp/schema.json')); [print(n) for n in d][:20]"

# Test bim.* queries
for code in \
  "bim.query().byType('IfcWall').count()" \
  "bim.query().byType('IfcWall').all()" \
  "bim.query().byType('IfcProject').first()" \
  "bim.query().byType('IfcSite').first()" \
  "bim.query().byType('IfcBuilding').first()" \
  "bim.query().byType('IfcBuildingStorey').all()" \
  "bim.query().spatial().all()" \
  "bim.query().byType('IfcWall').withProperties().all()" \
  "bim.query().byType('IfcWall').withMaterials().all()" \
  "bim.entity(1).all()"; do
  echo ">>> eval '$code'"
  ifc-lite eval /tmp/multi.ifc "$code" 2>&1 | head -20
  echo "---"
done
```

### 4.6 `run` (script file execution)
```bash
# Vytvor skript súbor a spusti
cat > /tmp/script.bim << 'EOF'
const walls = bim.query().byType('IfcWall').all();
console.log(`Found ${walls.length} walls`);
walls.forEach(w => console.log(`  - ${w.globalId}`));
EOF
ifc-lite run /tmp/multi.ifc /tmp/script.bim
```

### 4.7 Mutations
```bash
# Test property mutations
ifc-lite mutate /tmp/multi.ifc --set-property 1 Pset_WallCommon.FireRating "REI 60" --out /tmp/mutated.ifc
ifc-lite props /tmp/mutated.ifc --id 1
```

### 4.8 Diff a merge (enterprise features)
```bash
# Diff
ifc-lite diff /tmp/w1.ifc /tmp/w3.ifc --json > /tmp/diff.json
cat /tmp/diff.json | head -30

# Federation (3 models merged)
ifc-lite merge /tmp/w1.ifc /tmp/w2.ifc /tmp/w3.ifc --out /tmp/fed.ifc
ifc-lite info /tmp/fed.ifc --json
ifc-lite query /tmp/fed.ifc --type IfcWall --count   # očakávaj 3
```

### 4.9 Schema conversion
```bash
ifc-lite convert /tmp/multi.ifc --schema IFC2X3 --out /tmp/v2x3.ifc
ifc-lite convert /tmp/multi.ifc --schema IFC4X3 --out /tmp/v4x3.ifc
ifc-lite info /tmp/v2x3.ifc --json | grep -i schema
ifc-lite info /tmp/v4x3.ifc --json | grep -i schema
```

### 4.10 IDS validation
```bash
# Vytvor jednoduchý IDS spec a validuj
cat > /tmp/rules.ids << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<ids xmlns="http://standards.buildingsmart.org/IDS">
  <specification>
    <applicability>
      <entity>
        <name>
          <simpleValue>IfcWall</simpleValue>
        </name>
      </entity>
    </applicability>
    <requirements>
      <property>
        <name>
          <simpleValue>FireRating</simpleValue>
        </name>
      </property>
    </requirements>
  </specification>
</ids>
EOF
ifc-lite ids /tmp/multi.ifc /tmp/rules.ids --json | head -50
```

### 4.11 BCF (BIM Collaboration Format)
```bash
# Create BCF topic
ifc-lite bcf --help
ifc-lite bcf create --help
ifc-lite bcf create /tmp/multi.ifc --topic "Test issue" --out /tmp/test.bcf
ls -lh /tmp/test.bcf
unzip -l /tmp/test.bcf | head -20
```

### 4.12 Clash detection
```bash
# Vytvor 2 prekrývajúce sa prvky a zisti clash
ifc-lite create wall --start 0,0,0 --end 5,0,0 --height 3 --thickness 0.5 --out /tmp/a.ifc
ifc-lite create wall --start 2,0,0 --end 7,0,0 --height 3 --thickness 0.5 --out /tmp/b.ifc
ifc-lite merge /tmp/a.ifc /tmp/b.ifc --out /tmp/clash.ifc
ifc-lite clash /tmp/clash.ifc --matrix --bcf /tmp/clashes.bcf
ls -lh /tmp/clashes.bcf
cat /tmp/clash.ifc | head -1   # over že model je platný
```

### 4.13 bSDD (buildingSMART Data Dictionary)
```bash
ifc-lite bsdd --help
ifc-lite bsdd search "FireRating" 2>&1 | head -30
ifc-lite bsdd class "IfcWall" 2>&1 | head -30
```

### 4.14 Validate, stats, analyze, doctor
```bash
ifc-lite validate /tmp/multi.ifc --json
ifc-lite stats /tmp/multi.ifc --json
ifc-lite analyze /tmp/multi.ifc
ifc-lite doctor /tmp/multi.ifc --json
```

### 4.15 Diagnose-geometry, extract-entities, anonymize
```bash
ifc-lite diagnose-geometry /tmp/multi.ifc --json | head -30
ifc-lite extract-entities /tmp/multi.ifc --type IfcWall --json | head -20
ifc-lite anonymize /tmp/multi.ifc --out /tmp/anon.ifc
ifc-lite info /tmp/anon.ifc --json | grep -E "(author|organization|original)" 
```

### 4.16 Schedule, generate-spaces
```bash
ifc-lite schedule /tmp/multi.ifc --preset wall --out /tmp/schedule.csv
cat /tmp/schedule.csv | head -10
ifc-lite generate-spaces /tmp/multi.ifc --out /tmp/spaces.ifc
ifc-lite info /tmp/spaces.ifc --json | grep -i space
```

### 4.17 Export všetkých formátov
```bash
mkdir -p /tmp/exports
for fmt in csv json glb obj ifcx ifc usd hbjson parquet; do
  echo ">>> export $fmt"
  ifc-lite export /tmp/multi.ifc --format $fmt --out /tmp/exports/multi.$fmt 2>&1 | tail -3
  ls -lh /tmp/exports/multi.$fmt 2>/dev/null
done
ls -lh /tmp/exports/
```

---

## Fáza 5: Pattern E — MCP server cez stdio (overené, ale re-testuj)

```bash
# Stdio transport — over že stále funguje a zachytaj 125 tools presne
ifc-lite mcp /tmp/multi.ifc &
MCP_PID=$!
sleep 2
ps -p $MCP_PID && echo "RUNNING"

# Initialize
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | ifc-lite mcp /tmp/multi.ifc > /tmp/init.out 2>&1
cat /tmp/init.out | python3 -m json.tool 2>&1 | head -30

# tools/list (with proper sequence — initialize first, then initialized notification, then tools/list)
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'; \
 echo '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}'; \
 echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}') | ifc-lite mcp /tmp/multi.ifc > /tmp/tools.out 2>&1

# Spočítaj tools
grep -o '"name":"[a-z_]*"' /tmp/tools.out | wc -l   # očakávaj ~125
grep -o '"name":"[a-z_]*"' /tmp/tools.out | sort -u > /tmp/tool-names.txt
wc -l /tmp/tool-names.txt
head -40 /tmp/tool-names.txt

# Zastav background server
kill $MCP_PID 2>/dev/null
wait 2>/dev/null
```

---

## Fáza 6: Pattern E — MCP server cez HTTP transport (KRITICKÉ pre cross-machine)

```bash
# Spusti HTTP server
ifc-lite mcp /tmp/multi.ifc --transport http --port 8765 --token test123 &
HTTP_PID=$!
sleep 3
ps -p $HTTP_PID && echo "RUNNING"

# Test 1: Initialize s auth
curl -s -X POST http://localhost:8765 \
  -H "Authorization: Bearer test123" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
  -D /tmp/headers.txt > /tmp/init-http.out
cat /tmp/headers.txt   # zachytaj session ID z hlavičky
cat /tmp/init-http.out | python3 -m json.tool 2>&1 | head -30

# Extract session ID
SESSION_ID=$(grep -i "mcp-session-id" /tmp/headers.txt | awk '{print $2}' | tr -d '\r\n')
echo "SESSION_ID=$SESSION_ID"

# Test 2: tools/list s session ID
curl -s -X POST http://localhost:8765 \
  -H "Authorization: Bearer test123" \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' > /tmp/tools-http.out
grep -o '"name":"[a-z_]*"' /tmp/tools-http.out | wc -l   # očakávaj ~125

# Test 3: tools/call count_entities
curl -s -X POST http://localhost:8765 \
  -H "Authorization: Bearer test123" \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"count_entities","arguments":{"type":"IfcWall"}}}' \
  > /tmp/call-http.out
cat /tmp/call-http.out | python3 -m json.tool

# Test 4: Bez auth (mal by vrátiť 401)
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X POST http://localhost:8765 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'

# Test 5: Zlý token (mal by vrátiť 401)
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X POST http://localhost:8765 \
  -H "Authorization: Bearer wrong" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'

# Test 6: 0.0.0.0 binding — skús či funguje pre cross-machine (LAN access)
# Najprv zisti IP tvojho devpodu
IP=$(hostname -I | awk '{print $1}')
echo "DEVPOD IP: $IP"

# Zastav existujúci HTTP server
kill $HTTP_PID 2>/dev/null
sleep 1

# Skús s --host 0.0.0.0
ifc-lite mcp /tmp/multi.ifc --transport http --port 8765 --token test123 --host 0.0.0.0 &
HTTP_PID=$!
sleep 3

# Test z localhostu (mal by fungovať)
curl -s -o /dev/null -w "localhost: HTTP %{http_code}\n" -X POST http://localhost:8765 \
  -H "Authorization: Bearer test123" -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'

# Test z LAN IP (mal by fungovať ak --host 0.0.0.0 funguje)
curl -s -o /dev/null -w "LAN IP: HTTP %{http_code}\n" -X POST http://$IP:8765 \
  -H "Authorization: Bearer test123" -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'

kill $HTTP_PID 2>/dev/null
```

---

## Fáza 7: Claude Code MCP registration (KRITICKÉ)

```bash
# Register ifc-lite MCP server v Claude Code
claude mcp add ifc-lite -- npx -y @ifc-lite/cli mcp /tmp/multi.ifc

# Overenie
claude mcp list
claude mcp tools ifc-lite 2>&1 | head -50   # alebo otvor interaktívne

# Skús reálne query cez Claude Code (interaktívne, nie headless)
# Otvor claude, zadaj:
#   "How many walls are in the model?"
#   "List all IfcWall entities with their GlobalIds."
#   "What is the spatial hierarchy of this model?"
#   "Generate a CSV of all walls with their thickness."
#   "Check if any walls are missing a FireRating property."
```

**Zaznamenaj**: 
- či `claude mcp add` prešiel
- či `claude mcp list` ukazuje ifc-lite ako ✔ Connected
- či Claude v interaktívnej session reálne zavolal MCP tools
- aké odpovede dostal (presnosť, latencia)
- aké tool callovy sa zaznamenali

---

## Fáza 8: Python `rvt` binding (overenie)

```bash
pip install rvt 2>&1 | tail -3
python3 << 'EOF'
import rvt, json

# Ak máš reálny .rvt
import os
rvt_file = '/tmp/real.rvt' if os.path.exists('/tmp/real.rvt') else '/tmp/demo.rvt'

f = rvt.RevitFile(rvt_file)
print('=== Metadata ===')
print(f'version: {f.version}')
print(f'build: {f.build}')
print(f'guid: {f.guid}')
print(f'original_path: {f.original_path}')
print(f'part_atom_title: {f.part_atom_title}')

print('\\n=== Schema ===')
schema = f.schema_summary()
print(f'schema_summary: {schema}')

print('\\n=== Element counts ===')
counts = f.element_counts()
print(f'element_counts: {counts}')

print('\\n=== Stream names ===')
streams = f.stream_names()
print(f'num streams: {len(streams)}')
print(f'first 5 streams: {streams[:5]}')

print('\\n=== Decoded elements (if any) ===')
elements = f.decoded_elements()
print(f'num decoded elements: {len(elements) if hasattr(elements, "__len__") else "unknown"}')

print('\\n=== IFC export ===')
ifc_text = f.write_ifc(mode='geometry')
print(f'IFC length: {len(ifc_text)} chars')
print(f'IFC first 500 chars:\\n{ifc_text[:500]}')
EOF
```

---

## Fáza 9: Browser viewer (overenie WASM)

```bash
# ifc-lite má browser viewer — over ho lokálne
ifc-lite view --help
# (možno potrebujete inštaláciu, alebo to spustí local server)

# Skús otvoriť viewer:
# 1. Lokálne: ifc-lite view /tmp/multi.ifc (ak spustí local server, otvor v browseri)
# 2. Alebo skús ifclite.com / ifclite.dev z externe

# Ak to spustí local server, zaznamenaj:
# - port
# - či sa model reálne renderuje
# - performance (prvý render, full render)
# - môžeš urobiť screenshoty
```

---

## Fáza 10: Sandbox (QuickJS-in-WASM)

```bash
# Test sandboxed script execution
ifc-lite eval /tmp/multi.ifc --sandbox "bim.query().byType('IfcWall').count()" 2>&1 | head -20
# (over syntax z --help)

# Skús zložitejší skript:
cat > /tmp/script.bim << 'EOF'
const walls = bim.query().byType('IfcWall').all();
const doors = bim.query().byType('IfcDoor').all();
const windows = bim.query().byType('IfcWindow').all();

console.log(`Summary:`);
console.log(`  Walls: ${walls.length}`);
console.log(`  Doors: ${doors.length}`);
console.log(`  Windows: ${windows.length}`);

// Try to access something that should be blocked by sandbox
try {
  console.log(`  process.env.HOME: ${process.env.HOME}`);
} catch (e) {
  console.log(`  process.env blocked: ${e.message}`);
}

try {
  console.log(`  fs.readFileSync: ${typeof require('fs').readFileSync}`);
} catch (e) {
  console.log(`  require blocked: ${e.message}`);
}
EOF

ifc-lite run /tmp/multi.ifc /tmp/script.bim
```

---

## Fáza 11: Cloud source providers (ak majú zmysel)

```bash
# Test plugin_api (the type surface)
npm install @ifc-lite/plugin-api 2>&1 | tail -3

# Test source-dalux, source-dropbox, source-autodesk (len ak máš k nim prístup)
# Tieto vyžadujú cloud credentials — vynechaj ak nemáš
```

---

## Fáza 12: Errata — pripravenie pre v1.2

Po každej fáze zaznamenaj do `/tmp/errata-notes.md`:

```markdown
# Errata Notes for v1.2

## Fáza 1: Real .rvt file
- Sourced from: <source>
- File: <path>
- Size: <size>
- Revit version: <version>

## Fáza 2: Pattern D results
- rvt-info: <time>
- rvt-elements counts: <real counts vs book claims>
- rvt-ifc diagnostic: <exact vs bounding-box ratio>
- rvt-gltf: <time, file size>
- rvt-sheet: <time, file size>
- Python binding: <verified methods>

## Fáza 3: Synthetic fixture limitation
- Container layer: <verified>
- Schema layer: <verified>
- Element decoder: <confirmed total: 0>
- Diagnostics: <scaffold-only confirmed>

## Fáza 4: ifc-lite subcommand sweep
- Working subcommands: <list>
- Failing subcommands: <list with errors>
- Subcommands needing extra setup: <list>

## Fáza 5: MCP stdio
- Tool count: <real number>
- Initialize latency: <time>

## Fáza 6: MCP HTTP
- HTTP works: yes/no
- 0.0.0.0 binding: yes/no (CRITICAL for tomorrow)
- Auth works: yes/no
- LAN access works: yes/no

## Fáza 7: Claude Code MCP
- claude mcp add: success/fail
- claude mcp list shows Connected: yes/no
- Real tool calls from Claude: <list of queries, results>

## Fáza 8-11: Other findings
- Python binding API: <verified methods>
- Browser viewer: <works?>
- Sandbox: <what blocked?>
- Cloud sources: <skipped or tested>
```

---

## Master Deliverable (keď skončíš)

Pošli mi **jeden markdown report** s týmito sekciami:

1. **Reálny .rvt zdroj** — čo sa ti podarilo zohnať (URL, veľkosť, Revit verzia)
2. **Pattern D výsledky** — element counts, diagnostic accuracy, latencie
3. **Pattern D limitation** — potvrdené že syntetické fixtúry nevedú dekódovanie
4. **ifc-lite subcommand matrix** — tabuľka: subcommand | funguje | latencia | poznámka
5. **`ask` recipes** — kompletný zoznam, čo funguje, čo nie
6. **`eval` bim.* API** — aspoň 15 overených queries s outputom
7. **MCP stdio** — tool count, init latency, 125 tool names (aspoň top 30)
8. **MCP HTTP** — funguje? 0.0.0.0? auth?
9. **Claude Code integration** — `claude mcp add` výsledok, reálne tool calls
10. **Python binding** — overené metódy, príklady
11. **Surprises** — čokoľvek, čo prekvapilo (dobré alebo zlé)
12. **What didn't work** — čokoľvek čo zlyhalo s error messages

---

## Time budget

- Fáza 1-2: 20 min (kritické, ak sa podarí zohnať reálny .rvt)
- Fáza 3: 5 min
- Fáza 4: 30 min (najdlhšia — 30 subcommands)
- Fáza 5: 5 min
- Fáza 6: 10 min (HTTP transport + 0.0.0.0 binding)
- Fáza 7: 10 min (Claude Code registration + test queries)
- Fáza 8-11: 15 min
- Syntéza: 15 min

**Total: ~2 hodiny.** Ak to nestihneš všetko, priorita je:
1. Fáza 1 (reálny .rvt) — bez neho Pattern D neukážeš
2. Fáza 4.3 + 4.4 (subcommand sweep + ask recipes) — pre tomorrow demo
3. Fáza 6 (HTTP transport) — pre cross-machine scenario zajtra
4. Fáza 7 (Claude Code MCP) — pre overenie že reálny agent funguje

Ostatné môžeš preskočiť a ja ich otestujem z mojej strany cez agentov.

Choď na to. Som tu a keď prídeš s výsledkami, vyrobím **v1.2 knižky** s tvojimi reálnymi číslami + novými sekciami (bim.* API, HTTP transport, ask recipes).