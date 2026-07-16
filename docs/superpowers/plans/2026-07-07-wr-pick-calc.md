# Wild Rift Pick Calculator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar uma ferramenta web estática que sugere os 3 melhores picks para o usuário em tempo real durante o draft do Wild Rift, com base em counters, synergies e cobertura de lanes.

**Architecture:** App HTML + JS vanilla sem build step. Estado do draft (bans + picks dos dois times, posição do usuário, first-pick) é mantido em memória. A cada mudança, o motor de sugestão recalcula os top 3 picks disponíveis. Dados de campeões vêm de `data/champions.json`, gerado por um scraper Python avulso.

**Tech Stack:** HTML5, CSS3, JavaScript (ES modules, vanilla), Fuse.js (fuzzy search via CDN), Python 3 + requests + BeautifulSoup4 (scraper)

## Global Constraints

- Nenhum framework JS (React, Vue, etc.) — vanilla only
- Fuse.js via CDN (`<script src="https://cdn.jsdelivr.net/npm/fuse.js/dist/fuse.min.js">`)
- Sem servidor em runtime — servir via `file://` ou qualquer HTTP estático
- Todos os arquivos dentro de `wr-pick-calc/` na raiz do repo
- `data/champions.json` é gitignored se vazio; commitado com snapshot inicial após primeiro scrape
- Python 3.9+

---

### Task 1: Scaffolding do projeto

**Files:**
- Create: `wr-pick-calc/data/.gitkeep`
- Create: `wr-pick-calc/scraper/requirements.txt`
- Create: `wr-pick-calc/src/index.html` (estrutura HTML base)
- Create: `wr-pick-calc/src/style.css` (reset + variáveis CSS)
- Create: `wr-pick-calc/src/app.js` (stub vazio)
- Create: `wr-pick-calc/docs/2026-07-07-wr-pick-calc-design.md`

**Interfaces:**
- Produces: estrutura de pastas e HTML shell que os demais tasks preenchem

- [ ] **Step 1: Criar estrutura de pastas**

```bash
mkdir -p wr-pick-calc/data
mkdir -p wr-pick-calc/scraper
mkdir -p wr-pick-calc/src
mkdir -p wr-pick-calc/docs
touch wr-pick-calc/data/.gitkeep
```

- [ ] **Step 2: Criar requirements.txt**

```txt
requests==2.31.0
beautifulsoup4==4.12.3
```

Salvar em `wr-pick-calc/scraper/requirements.txt`.

- [ ] **Step 3: Criar index.html base**

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WR Pick Calc</title>
  <link rel="stylesheet" href="style.css">
  <script src="https://cdn.jsdelivr.net/npm/fuse.js/dist/fuse.min.js"></script>
</head>
<body>
  <div id="app">
    <!-- preenchido pelo app.js -->
  </div>
  <script type="module" src="app.js"></script>
</body>
</html>
```

Salvar em `wr-pick-calc/src/index.html`.

- [ ] **Step 4: Criar style.css com reset e variáveis**

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #0a0e1a;
  --surface: #111827;
  --border: #1f2d45;
  --ally: #1a3a5c;
  --ally-active: #2563eb;
  --enemy: #3a1a1a;
  --enemy-active: #dc2626;
  --text: #e2e8f0;
  --text-muted: #64748b;
  --gold: #f59e0b;
  --radius: 6px;
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Segoe UI', system-ui, sans-serif;
  min-height: 100vh;
}

#app {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 16px;
}
```

Salvar em `wr-pick-calc/src/style.css`.

- [ ] **Step 5: Criar app.js stub**

```js
// Wild Rift Pick Calculator
// Módulos: state.js (gerenciado inline), engine.js importado, ui.js importado
// Ponto de entrada — inicializa a UI após carregar champions.json

async function main() {
  console.log('WR Pick Calc carregado');
}

main();
```

Salvar em `wr-pick-calc/src/app.js`.

- [ ] **Step 6: Criar doc de design**

Copiar o conteúdo do spec de brainstorming para `wr-pick-calc/docs/2026-07-07-wr-pick-calc-design.md`.

- [ ] **Step 7: Commit**

```bash
git add wr-pick-calc/
git commit -m "feat: scaffold wr-pick-calc project structure"
```

---

### Task 2: Scraper Python

**Files:**
- Create: `wr-pick-calc/scraper/scrape.py`

**Interfaces:**
- Produces: `wr-pick-calc/data/champions.json` com schema:
  ```json
  [{ "id": "zed", "name": "Zed", "lanes": ["mid","jungle"], "counters": ["fizz"], "counteredBy": ["malzahar"], "synergies": ["jinx"] }]
  ```

- [ ] **Step 1: Instalar dependências**

```bash
cd wr-pick-calc/scraper
pip install -r requirements.txt
```

Esperado: instalação sem erros.

- [ ] **Step 2: Escrever scrape.py**

```python
import json
import time
import re
from pathlib import Path
import requests
from bs4 import BeautifulSoup

BASE = "https://wildrift.gg"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; wr-pick-calc/1.0)"}
OUT = Path(__file__).parent.parent / "data" / "champions.json"

LANE_MAP = {
    "baron": "baron",
    "jungle": "jungle",
    "mid": "mid",
    "dragon": "dragon",
    "support": "support",
}

def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())

def get_champion_list() -> list[dict]:
    r = requests.get(f"{BASE}/champions/", headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    champs = []
    for a in soup.select("a[href*='/champions/']"):
        href = a["href"]
        match = re.match(r"/champions/([a-z0-9-]+)/?$", href)
        if not match:
            continue
        slug = match.group(1)
        name_el = a.select_one("[class*='name'], h3, h4, span")
        name = name_el.get_text(strip=True) if name_el else slug.replace("-", " ").title()
        if slug and name:
            champs.append({"slug": slug, "name": name})
    seen = set()
    return [c for c in champs if not (c["slug"] in seen or seen.add(c["slug"]))]

def get_champion_data(slug: str) -> dict | None:
    url = f"{BASE}/champions/{slug}/"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"  ERRO ao buscar {slug}: {e}")
        return None
    soup = BeautifulSoup(r.text, "html.parser")

    # Lanes
    lanes = []
    for el in soup.select("[class*='role'], [class*='lane'], [class*='position']"):
        txt = el.get_text(strip=True).lower()
        for lane in LANE_MAP:
            if lane in txt:
                lanes.append(LANE_MAP[lane])
    lanes = list(dict.fromkeys(lanes))  # dedup preservando ordem

    # Counters / counteredBy
    counters, countered_by = [], []
    for section in soup.select("[class*='counter'], [class*='matchup']"):
        header = section.get_text(strip=True).lower()
        names = [a.get_text(strip=True) for a in section.select("a, [class*='champion']")]
        if "strong against" in header or "counters" in header:
            counters.extend(slugify(n) for n in names if n)
        elif "weak against" in header or "countered" in header:
            countered_by.extend(slugify(n) for n in names if n)

    # Synergies
    synergies = []
    for section in soup.select("[class*='synerg']"):
        synergies.extend(slugify(a.get_text(strip=True)) for a in section.select("a, [class*='champion']") if a.get_text(strip=True))

    return {
        "lanes": lanes or ["mid"],
        "counters": list(dict.fromkeys(counters)),
        "counteredBy": list(dict.fromkeys(countered_by)),
        "synergies": list(dict.fromkeys(synergies)),
    }

def main():
    print("Buscando lista de campeões...")
    champs = get_champion_list()
    print(f"  {len(champs)} campeões encontrados")

    result = []
    for i, c in enumerate(champs, 1):
        print(f"  [{i}/{len(champs)}] {c['name']}...", end=" ")
        data = get_champion_data(c["slug"])
        if data:
            result.append({"id": c["slug"], "name": c["name"], **data})
            print("ok")
        else:
            print("skip")
        time.sleep(0.5)  # rate limit gentil

    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\nSalvo em {OUT} ({len(result)} campeões)")

if __name__ == "__main__":
    main()
```

Salvar em `wr-pick-calc/scraper/scrape.py`.

- [ ] **Step 3: Executar scraper e validar output**

```bash
cd wr-pick-calc/scraper
python scrape.py
```

Esperado: arquivo `data/champions.json` criado com ≥50 entradas. Validar manualmente 2-3 campeões conhecidos (ex: Zed, Jinx, Yasuo) para conferir campos não vazios.

> **Nota:** Se o wildrift.gg usar JS heavy rendering e o scraper retornar listas vazias, substituir `requests` + `BeautifulSoup` por `playwright` (ver nota abaixo). Isso é esperado e não é um bug no código.

**Fallback com Playwright:**
```bash
pip install playwright
playwright install chromium
```

No `scrape.py`, substituir o bloco de `requests.get` por:
```python
from playwright.sync_api import sync_playwright
def fetch(url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        html = page.content()
        browser.close()
    return html
```

- [ ] **Step 4: Commit**

```bash
git add wr-pick-calc/scraper/ wr-pick-calc/data/champions.json
git commit -m "feat: add wildrift.gg scraper and initial champions.json"
```

---

### Task 3: Estado do draft + lógica de ordem serpentina

**Files:**
- Create: `wr-pick-calc/src/state.js`

**Interfaces:**
- Produces:
  ```js
  // state.js exports:
  createDraft(userIsFirstPick: boolean, userLane: string): DraftState
  setSlot(state: DraftState, slotId: string, championId: string): DraftState
  getActiveSlot(state: DraftState): string | null  // slotId ou null se draft completo
  getAvailable(state: DraftState, champions: Champion[]): Champion[]
  ```

  ```js
  // Tipos internos (não exportados, documentados aqui para referência):
  // DraftState = {
  //   userIsFirstPick: boolean,
  //   userLane: string,
  //   userSlotId: string | null,  // slotId que pertence ao usuário
  //   slots: { [slotId]: string | null },  // slotId → championId | null
  //   sequence: string[],  // ordem dos slotIds no draft
  //   currentIndex: number
  // }
  //
  // slotId = "ally-ban-0" | "ally-ban-1" | ... | "ally-ban-3"
  //        | "enemy-ban-0" | ... | "enemy-ban-3"
  //        | "ally-pick-0" | ... | "ally-pick-4"
  //        | "enemy-pick-0" | ... | "enemy-pick-4"
  ```

- [ ] **Step 1: Criar state.js**

```js
// Ordem serpentina Wild Rift:
// Bans: ally0 enemy0 ally1 enemy1 ally2 enemy2 ally3 enemy3
// Picks: ally0 enemy0 enemy1 ally1 ally2 enemy2 enemy3 ally3 ally4 enemy4

const BAN_SEQUENCE = [
  'ally-ban-0', 'enemy-ban-0',
  'ally-ban-1', 'enemy-ban-1',
  'ally-ban-2', 'enemy-ban-2',
  'ally-ban-3', 'enemy-ban-3',
];

const PICK_SEQUENCE_FIRST = [
  'ally-pick-0',
  'enemy-pick-0', 'enemy-pick-1',
  'ally-pick-1', 'ally-pick-2',
  'enemy-pick-2', 'enemy-pick-3',
  'ally-pick-3', 'ally-pick-4',
  'enemy-pick-4',
];

const PICK_SEQUENCE_SECOND = [
  'enemy-pick-0',
  'ally-pick-0', 'ally-pick-1',
  'enemy-pick-1', 'enemy-pick-2',
  'ally-pick-2', 'ally-pick-3',
  'enemy-pick-3', 'enemy-pick-4',
  'ally-pick-4',
];

export function createDraft(userIsFirstPick, userLane) {
  const pickSeq = userIsFirstPick ? PICK_SEQUENCE_FIRST : PICK_SEQUENCE_SECOND;
  const sequence = [...BAN_SEQUENCE, ...pickSeq];
  const slots = {};
  sequence.forEach(id => { slots[id] = null; });
  return {
    userIsFirstPick,
    userLane,
    userSlotId: null,
    slots,
    sequence,
    currentIndex: 0,
  };
}

export function setSlot(state, slotId, championId) {
  const newSlots = { ...state.slots, [slotId]: championId };
  const newIndex = state.currentIndex + 1;
  return { ...state, slots: newSlots, currentIndex: newIndex };
}

export function setUserSlot(state, slotId) {
  return { ...state, userSlotId: slotId };
}

export function getActiveSlot(state) {
  if (state.currentIndex >= state.sequence.length) return null;
  return state.sequence[state.currentIndex];
}

export function getAvailable(state, champions) {
  const used = new Set(Object.values(state.slots).filter(Boolean));
  return champions.filter(c => !used.has(c.id));
}

export function getAllyPicks(state) {
  return Object.entries(state.slots)
    .filter(([id, val]) => id.startsWith('ally-pick') && val)
    .map(([, val]) => val);
}

export function getEnemyPicks(state) {
  return Object.entries(state.slots)
    .filter(([id, val]) => id.startsWith('enemy-pick') && val)
    .map(([, val]) => val);
}

export function getBanned(state) {
  return Object.entries(state.slots)
    .filter(([id, val]) => id.includes('-ban-') && val)
    .map(([, val]) => val);
}
```

Salvar em `wr-pick-calc/src/state.js`.

- [ ] **Step 2: Testar manualmente no console do browser**

Abrir `index.html`, abrir DevTools → Console:
```js
import { createDraft, getActiveSlot, setSlot } from './state.js';
const s = createDraft(true, 'mid');
console.log(getActiveSlot(s)); // "ally-ban-0"
const s2 = setSlot(s, 'ally-ban-0', 'zed');
console.log(getActiveSlot(s2)); // "enemy-ban-0"
```

Esperado: sequência correta de slotIds conforme o draft avança.

- [ ] **Step 3: Commit**

```bash
git add wr-pick-calc/src/state.js
git commit -m "feat: add draft state machine with serpentine order"
```

---

### Task 4: Motor de sugestão

**Files:**
- Create: `wr-pick-calc/src/engine.js`

**Interfaces:**
- Consumes:
  - `getAllyPicks`, `getEnemyPicks`, `getBanned`, `getAvailable` de `state.js`
  - `DraftState` e `Champion[]` (schema de `champions.json`)
- Produces:
  ```js
  // engine.js exports:
  suggest(state: DraftState, champions: Champion[]): Suggestion[]
  // Suggestion = { id: string, name: string, score: number, reasons: string[] }
  // Retorna array de 3 elementos (ou menos se não houver disponíveis)
  ```

- [ ] **Step 1: Criar engine.js**

```js
import { getAllyPicks, getEnemyPicks, getBanned, getAvailable } from './state.js';

export function suggest(state, champions) {
  const allyIds = new Set(getAllyPicks(state));
  const enemyIds = new Set(getEnemyPicks(state));
  const bannedIds = new Set(getBanned(state));

  // Lanes já cobertas pelo time aliado
  const coveredLanes = new Set();
  allyIds.forEach(id => {
    const c = champions.find(x => x.id === id);
    if (c) c.lanes.forEach(l => coveredLanes.add(l));
  });

  const available = getAvailable(state, champions);

  const scored = available.map(candidate => {
    let score = 0;
    const reasons = [];

    // Score individual: counter vs inimigos
    enemyIds.forEach(eid => {
      if (candidate.counters.includes(eid)) {
        score += 3;
        const name = champions.find(c => c.id === eid)?.name ?? eid;
        reasons.push(`countera ${name}`);
      }
      if (candidate.counteredBy.includes(eid)) {
        score -= 3;
        const name = champions.find(c => c.id === eid)?.name ?? eid;
        reasons.push(`fraco contra ${name}`);
      }
    });

    // Score individual: cobre lane do usuário
    if (state.userLane && candidate.lanes.includes(state.userLane)) {
      score += 2;
      reasons.push(`cobre ${state.userLane}`);
    }

    // Score de time: sinergia com aliados
    allyIds.forEach(aid => {
      if (candidate.synergies.includes(aid)) {
        score += 2;
        const name = champions.find(c => c.id === aid)?.name ?? aid;
        reasons.push(`sinergia com ${name}`);
      }
    });

    // Score de time: cobre lane descoberta
    candidate.lanes.forEach(lane => {
      if (!coveredLanes.has(lane)) {
        score += 1;
        if (!reasons.find(r => r.includes('cobre'))) {
          reasons.push(`cobre ${lane} livre`);
        }
      }
    });

    return { id: candidate.id, name: candidate.name, score, reasons };
  });

  return scored
    .sort((a, b) => b.score - a.score)
    .slice(0, 3);
}
```

Salvar em `wr-pick-calc/src/engine.js`.

- [ ] **Step 2: Testar manualmente no console**

Após carregar `champions.json`, no console:
```js
import { createDraft, setSlot } from './state.js';
import { suggest } from './engine.js';
// Simular: inimigo Zed selecionado
let s = createDraft(true, 'mid');
s = setSlot(s, 'ally-ban-0', '__none__'); // pular bans rapidamente
// ... avançar até enemy-pick-0
s = { ...s, slots: { ...s.slots, 'enemy-pick-0': 'zed' }, currentIndex: 10 };
const champs = await fetch('../data/champions.json').then(r => r.json());
const top3 = suggest(s, champs);
console.log(top3.map(x => `${x.name}: ${x.score} — ${x.reasons.join(', ')}`));
```

Esperado: 3 campeões listados, com razões coerentes (campeão que countera Zed deve aparecer com score positivo).

- [ ] **Step 3: Commit**

```bash
git add wr-pick-calc/src/engine.js
git commit -m "feat: add pick suggestion engine with scoring"
```

---

### Task 5: Interface — layout do draft

**Files:**
- Modify: `wr-pick-calc/src/index.html`
- Modify: `wr-pick-calc/src/style.css`
- Modify: `wr-pick-calc/src/app.js`

**Interfaces:**
- Consumes: `createDraft`, `setSlot`, `setUserSlot`, `getActiveSlot` de `state.js`; `suggest` de `engine.js`
- Produces: layout visual completo com colunas de ban/pick + painel de recomendações

- [ ] **Step 1: Atualizar index.html com estrutura semântica**

Substituir o conteúdo de `<body>` por:

```html
<body>
  <div id="app">
    <header id="setup" class="setup-bar">
      <label class="toggle-label">
        <input type="checkbox" id="first-pick-toggle">
        <span>Meu time faz o first pick</span>
      </label>
      <div class="lane-select">
        <span>Minha lane:</span>
        <select id="lane-select">
          <option value="">— selecione —</option>
          <option value="baron">Baron</option>
          <option value="jungle">Jungle</option>
          <option value="mid">Mid</option>
          <option value="dragon">Dragon</option>
          <option value="support">Support</option>
        </select>
      </div>
      <button id="start-btn" disabled>Iniciar Draft</button>
    </header>

    <main id="draft-area" class="draft-area hidden">
      <section class="team ally">
        <h2>Meu Time</h2>
        <div class="bans" id="ally-bans"></div>
        <div class="picks" id="ally-picks"></div>
      </section>

      <section class="recommendations" id="recommendations">
        <h2>Sugestões</h2>
        <div id="rec-cards"></div>
      </section>

      <section class="team enemy">
        <h2>Time Inimigo</h2>
        <div class="bans" id="enemy-bans"></div>
        <div class="picks" id="enemy-picks"></div>
      </section>
    </main>

    <!-- Modal de busca -->
    <div id="search-modal" class="modal hidden">
      <div class="modal-box">
        <input id="champ-search" type="text" placeholder="Buscar campeão..." autocomplete="off">
        <ul id="search-results"></ul>
      </div>
    </div>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/fuse.js/dist/fuse.min.js"></script>
  <script type="module" src="app.js"></script>
</body>
```

- [ ] **Step 2: Adicionar estilos de layout ao style.css**

Acrescentar ao final de `style.css`:

```css
/* Setup bar */
.setup-bar {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 16px;
  background: var(--surface);
  border-radius: var(--radius);
  margin-bottom: 24px;
  border: 1px solid var(--border);
}
.toggle-label { display: flex; align-items: center; gap: 8px; cursor: pointer; }
.toggle-label input { width: 18px; height: 18px; cursor: pointer; }
.lane-select { display: flex; align-items: center; gap: 8px; }
.lane-select select {
  background: var(--bg);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 6px 10px;
}
#start-btn {
  margin-left: auto;
  background: var(--ally-active);
  color: #fff;
  border: none;
  border-radius: var(--radius);
  padding: 8px 20px;
  cursor: pointer;
  font-size: 14px;
}
#start-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* Draft area */
.draft-area {
  display: grid;
  grid-template-columns: 1fr 220px 1fr;
  gap: 16px;
  align-items: start;
}
.hidden { display: none !important; }

/* Teams */
.team h2 { font-size: 13px; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); margin-bottom: 12px; }
.bans { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 12px; }
.picks { display: flex; flex-direction: column; gap: 8px; }

/* Slots */
.slot {
  border-radius: var(--radius);
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
  user-select: none;
  font-size: 13px;
  color: var(--text-muted);
}
.slot:hover { border-color: #4b5563; }
.slot.active {
  border-color: var(--gold);
  box-shadow: 0 0 0 2px var(--gold);
  color: var(--gold);
}
.slot.filled { color: var(--text); border-color: var(--border); cursor: default; }
.slot.user-slot { border-style: dashed; }

/* Ban slot */
.slot.ban-slot { width: 44px; height: 44px; font-size: 11px; }
/* Pick slot */
.slot.pick-slot { height: 56px; width: 100%; }

.ally .slot.active { border-color: var(--ally-active); box-shadow: 0 0 0 2px var(--ally-active); color: var(--ally-active); }
.enemy .slot.active { border-color: var(--enemy-active); box-shadow: 0 0 0 2px var(--enemy-active); color: var(--enemy-active); }

/* Recommendations */
.recommendations h2 { font-size: 13px; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); margin-bottom: 12px; }
#rec-cards { display: flex; flex-direction: column; gap: 10px; }
.rec-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px;
}
.rec-card .champ-name { font-weight: 600; font-size: 15px; }
.rec-card .score { font-size: 12px; color: var(--gold); margin: 2px 0 6px; }
.rec-card .reasons { list-style: none; }
.rec-card .reasons li { font-size: 12px; color: var(--text-muted); }
.rec-card .reasons li::before { content: "› "; color: var(--gold); }

/* Modal de busca */
.modal {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
.modal-box {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  width: 320px;
  padding: 16px;
}
#champ-search {
  width: 100%;
  background: var(--bg);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 10px;
  font-size: 15px;
  margin-bottom: 10px;
}
#search-results { list-style: none; max-height: 280px; overflow-y: auto; }
#search-results li {
  padding: 8px 10px;
  cursor: pointer;
  border-radius: var(--radius);
  font-size: 14px;
}
#search-results li:hover, #search-results li.selected { background: var(--border); }
```

- [ ] **Step 3: Verificar visualmente**

Abrir `src/index.html` no browser. Conferir:
- Setup bar visível com toggle, lane select e botão desabilitado
- Ao selecionar uma lane, botão deve habilitar (ainda não funciona — isso vem no app.js do próximo step)

- [ ] **Step 4: Commit**

```bash
git add wr-pick-calc/src/index.html wr-pick-calc/src/style.css
git commit -m "feat: add draft layout HTML and CSS"
```

---

### Task 6: app.js — orquestração completa

**Files:**
- Modify: `wr-pick-calc/src/app.js`

**Interfaces:**
- Consumes: `state.js` (todos os exports), `engine.js` (suggest), Fuse.js (global), `data/champions.json`
- Produces: aplicação interativa completa

- [ ] **Step 1: Reescrever app.js**

```js
import {
  createDraft, setSlot, setUserSlot,
  getActiveSlot, getAvailable,
} from './state.js';
import { suggest } from './engine.js';

let champions = [];
let state = null;
let activeSlotId = null;
let fuse = null;

// ── Setup ──────────────────────────────────────────────────────────────────

const toggle = document.getElementById('first-pick-toggle');
const laneSelect = document.getElementById('lane-select');
const startBtn = document.getElementById('start-btn');
const setupBar = document.getElementById('setup');
const draftArea = document.getElementById('draft-area');
const modal = document.getElementById('search-modal');
const searchInput = document.getElementById('champ-search');
const searchResults = document.getElementById('search-results');

laneSelect.addEventListener('change', () => {
  startBtn.disabled = !laneSelect.value;
});

startBtn.addEventListener('click', initDraft);

async function main() {
  champions = await fetch('../data/champions.json').then(r => r.json());
  fuse = new Fuse(champions, { keys: ['name'], threshold: 0.4 });
}

// ── Draft init ─────────────────────────────────────────────────────────────

function initDraft() {
  const userIsFirstPick = toggle.checked;
  const userLane = laneSelect.value;
  state = createDraft(userIsFirstPick, userLane);
  setupBar.classList.add('hidden');
  draftArea.classList.remove('hidden');
  renderDraft();
}

// ── Render ─────────────────────────────────────────────────────────────────

function renderDraft() {
  renderTeam('ally');
  renderTeam('enemy');
  renderRecommendations();
  highlightActive();
}

function renderTeam(side) {
  const bansEl = document.getElementById(`${side}-bans`);
  const picksEl = document.getElementById(`${side}-picks`);
  bansEl.innerHTML = '';
  picksEl.innerHTML = '';

  for (let i = 0; i < 4; i++) {
    const id = `${side}-ban-${i}`;
    bansEl.appendChild(makeSlot(id, 'ban-slot'));
  }
  for (let i = 0; i < 5; i++) {
    const id = `${side}-pick-${i}`;
    picksEl.appendChild(makeSlot(id, 'pick-slot'));
  }
}

function makeSlot(slotId, cls) {
  const el = document.createElement('div');
  el.className = `slot ${cls}`;
  el.dataset.slot = slotId;
  const val = state.slots[slotId];
  if (val) {
    const champ = champions.find(c => c.id === val);
    el.textContent = champ ? champ.name : val;
    el.classList.add('filled');
  } else {
    el.textContent = '+';
    el.addEventListener('click', () => openSearch(slotId));
  }
  if (slotId === state.userSlotId) el.classList.add('user-slot');
  return el;
}

function highlightActive() {
  document.querySelectorAll('.slot.active').forEach(el => el.classList.remove('active'));
  const active = getActiveSlot(state);
  if (active) {
    const el = document.querySelector(`[data-slot="${active}"]`);
    if (el) el.classList.add('active');
  }
}

function renderRecommendations() {
  const cards = document.getElementById('rec-cards');
  cards.innerHTML = '';

  // Só mostra se slot do usuário ainda não foi preenchido
  if (state.userSlotId && state.slots[state.userSlotId]) return;

  const top3 = suggest(state, champions);
  top3.forEach(s => {
    const card = document.createElement('div');
    card.className = 'rec-card';
    card.innerHTML = `
      <div class="champ-name">${s.name}</div>
      <div class="score">score: ${s.score}</div>
      <ul class="reasons">${s.reasons.map(r => `<li>${r}</li>`).join('')}</ul>
    `;
    cards.appendChild(card);
  });
}

// ── Search modal ───────────────────────────────────────────────────────────

function openSearch(slotId) {
  activeSlotId = slotId;

  // Marcar slot do usuário se ainda não marcado e for slot de pick aliado
  if (!state.userSlotId && slotId.startsWith('ally-pick')) {
    state = setUserSlot(state, slotId);
  }

  modal.classList.remove('hidden');
  searchInput.value = '';
  renderSearchResults('');
  searchInput.focus();
}

function closeModal() {
  modal.classList.add('hidden');
  activeSlotId = null;
}

modal.addEventListener('click', e => {
  if (e.target === modal) closeModal();
});

searchInput.addEventListener('input', () => {
  renderSearchResults(searchInput.value);
});

searchInput.addEventListener('keydown', e => {
  const items = searchResults.querySelectorAll('li');
  const selected = searchResults.querySelector('li.selected');
  if (e.key === 'ArrowDown') {
    const next = selected ? selected.nextElementSibling : items[0];
    selected?.classList.remove('selected');
    next?.classList.add('selected');
    e.preventDefault();
  } else if (e.key === 'ArrowUp') {
    const prev = selected?.previousElementSibling;
    selected?.classList.remove('selected');
    prev?.classList.add('selected');
    e.preventDefault();
  } else if (e.key === 'Enter') {
    const sel = searchResults.querySelector('li.selected');
    if (sel) sel.click();
  } else if (e.key === 'Escape') {
    closeModal();
  }
});

function renderSearchResults(query) {
  searchResults.innerHTML = '';
  const available = getAvailable(state, champions);
  const results = query
    ? fuse.search(query, { limit: 8 }).map(r => r.item).filter(c => available.find(a => a.id === c.id))
    : available.slice(0, 8);

  results.forEach(c => {
    const li = document.createElement('li');
    li.textContent = c.name;
    li.addEventListener('click', () => selectChampion(c.id));
    searchResults.appendChild(li);
  });
}

function selectChampion(championId) {
  state = setSlot(state, activeSlotId, championId);
  closeModal();
  renderDraft();
}

main();
```

Salvar em `wr-pick-calc/src/app.js`.

- [ ] **Step 2: Testar fluxo completo**

1. Abrir `src/index.html` no browser
2. Selecionar lane "Mid", deixar first-pick desmarcado → clicar "Iniciar Draft"
3. Confirmar que o slot `enemy-ban-0` (time inimigo) está destacado em vermelho
4. Clicar em qualquer slot inimigo → digitar "ze" → confirmar que "Zed" aparece
5. Selecionar Zed → confirmar que slot preenchido e próximo slot acende
6. Clicar num slot aliado → confirmar que é marcado como "meu slot" (borda tracejada)
7. Confirmar que painel de recomendações mostra 3 cards com score e razões
8. Digitar "ez" → confirmar que "Ezreal" aparece (fuzzy)
9. Banir um campeão → confirmar que ele desaparece da busca

- [ ] **Step 3: Commit**

```bash
git add wr-pick-calc/src/app.js
git commit -m "feat: complete app.js with draft orchestration and UI"
```

---

### Task 7: Polimento e README

**Files:**
- Create: `wr-pick-calc/README.md`
- Modify: `wr-pick-calc/src/style.css` (ajustes finais se necessário)

- [ ] **Step 1: Criar README.md**

```markdown
# wr-pick-calc

Calculadora de picks para Wild Rift ranked. Sugere os 3 melhores campeões em tempo real durante o draft, com base em counters, synergies e cobertura de lanes.

## Uso

1. Abrir `src/index.html` no browser
2. Marcar se seu time faz o first pick e selecionar sua lane
3. Replicar os picks/bans do jogo na ordem em que acontecem
4. As 3 sugestões atualizam a cada mudança

## Atualizar dados (novo patch)

```bash
cd scraper
pip install -r requirements.txt
python scrape.py
```

O arquivo `data/champions.json` será atualizado.
```

- [ ] **Step 2: Verificação final end-to-end**

1. Abrir `src/index.html`
2. Simular um draft completo (todos os 8 bans + primeiros 3 picks de cada lado)
3. Confirmar que as sugestões param de atualizar após o usuário preencher seu slot
4. Confirmar que a ordem serpentina está correta (conferir contra a sequência documentada no plano)
5. Confirmar que campeões banidos não aparecem como sugestão nem na busca

- [ ] **Step 3: Commit final**

```bash
git add wr-pick-calc/README.md
git commit -m "feat: complete wr-pick-calc — pick calculator for Wild Rift"
```
