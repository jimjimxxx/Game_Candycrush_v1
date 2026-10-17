"use strict";

// Python sources served next to this page (copied there by the Pages workflow).
const PY_FILES = {
  "candycrush/__init__.py": "py/candycrush/__init__.py",
  "candycrush/board.py": "py/candycrush/board.py",
  "candycrush/game.py": "py/candycrush/game.py",
  "candycrush/agents.py": "py/candycrush/agents.py",
  "bridge.py": "bridge.py",
};
const SYMBOLS = "RYGBPCWO";
const STEP_MS = 380;

const boardEl = document.getElementById("board");
const scoreEl = document.getElementById("score");
const movesEl = document.getElementById("moves");
const messageEl = document.getElementById("message");
const hintBtn = document.getElementById("hint");
const autoBtn = document.getElementById("auto");
const newBtn = document.getElementById("new");

let bridge = null;
let state = null;
let selected = null;
let busy = false;
let autoplay = false;
let pointerStart = null;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const call = (name, ...args) => JSON.parse(bridge[name](...args));
const adjacent = (a, b) => Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]) === 1;

function say(text) {
  messageEl.textContent = text;
}

function render(grid, marks = {}) {
  const rows = grid.length;
  const cols = grid[0].length;
  boardEl.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
  boardEl.replaceChildren();
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const v = grid[r][c];
      const cell = document.createElement("button");
      cell.className = `cell t${v}`;
      cell.dataset.r = r;
      cell.dataset.c = c;
      cell.setAttribute("aria-label", `row ${r}, column ${c}, ${SYMBOLS[v - 1] || v}`);
      cell.textContent = SYMBOLS[v - 1] || v;
      const key = `${r},${c}`;
      if (marks[key]) cell.classList.add(marks[key]);
      if (selected && selected[0] === r && selected[1] === c) cell.classList.add("selected");
      boardEl.appendChild(cell);
    }
  }
}

function showStats() {
  scoreEl.textContent = state.score;
  movesEl.textContent = state.moves_left;
  const idle = !busy && !state.over;
  hintBtn.disabled = !idle;
  autoBtn.disabled = state.over;
  autoBtn.textContent = autoplay ? "Stop the agent" : "Let the greedy agent play";
  newBtn.disabled = busy;
}

function seedFromUrl() {
  const s = new URLSearchParams(location.search).get("seed");
  return s !== null && /^\d+$/.test(s) ? Number(s) : null;
}

function newGame(seed = null) {
  autoplay = false;
  selected = null;
  state = call("new_game", seed);
  render(state.grid);
  showStats();
  say(seed === null ? "Pick two neighbouring candies to swap." : `Seed ${seed}. Pick two neighbouring candies to swap.`);
}

async function doMove(a, b) {
  busy = true;
  selected = null;
  showStats();
  const res = call("play", a[0], a[1], b[0], b[1]);
  if (res.error) {
    say(`Can't do that: ${res.error}.`);
  } else if (!res.valid) {
    render(res.grid, { [a.join()]: "shake", [b.join()]: "shake" });
    say("No match, swap undone. That still used a move.");
    await sleep(STEP_MS);
  } else {
    for (const step of res.steps) {
      render(step.grid);
      await sleep(STEP_MS / 2);
      const marks = {};
      for (const [r, c] of step.cleared) marks[`${r},${c}`] = "pop";
      render(step.grid, marks);
      await sleep(STEP_MS);
    }
    const waves = res.waves.join(" + ");
    say(`Cleared ${waves} candies, +${res.points} points.` + (res.reshuffled ? " No moves left, so the board was reshuffled." : ""));
  }
  state = res;
  render(state.grid);
  busy = false;
  if (state.over) {
    autoplay = false;
    say(`Game over. Final score: ${state.score}.`);
  }
  showStats();
}

async function runAgent() {
  autoplay = true;
  showStats();
  while (autoplay && !state.over) {
    const [a, b] = call("hint");
    render(state.grid, { [a.join()]: "hinted", [b.join()]: "hinted" });
    await sleep(STEP_MS);
    if (!autoplay) break;
    await doMove(a, b);
    await sleep(STEP_MS / 2);
  }
  autoplay = false;
  showStats();
}

function cellOf(target) {
  const el = target.closest(".cell");
  return el ? [Number(el.dataset.r), Number(el.dataset.c)] : null;
}

function choose(cell) {
  if (busy || autoplay || state.over || !cell) return;
  if (selected && adjacent(selected, cell)) {
    doMove(selected, cell);
    return;
  }
  selected = selected && selected[0] === cell[0] && selected[1] === cell[1] ? null : cell;
  render(state.grid);
}

boardEl.addEventListener("pointerdown", (e) => {
  pointerStart = { cell: cellOf(e.target), x: e.clientX, y: e.clientY };
});

boardEl.addEventListener("pointerup", (e) => {
  if (!pointerStart || !pointerStart.cell) return;
  const dx = e.clientX - pointerStart.x;
  const dy = e.clientY - pointerStart.y;
  const start = pointerStart.cell;
  pointerStart = null;
  if (Math.max(Math.abs(dx), Math.abs(dy)) < 18) {
    choose(start);
    return;
  }
  if (busy || autoplay || state.over) return;
  const step = Math.abs(dx) > Math.abs(dy) ? [0, Math.sign(dx)] : [Math.sign(dy), 0];
  const target = [start[0] + step[0], start[1] + step[1]];
  if (target[0] < 0 || target[1] < 0 || target[0] >= state.grid.length || target[1] >= state.grid[0].length) return;
  doMove(start, target);
});

hintBtn.addEventListener("click", () => {
  const [a, b] = call("hint");
  render(state.grid, { [a.join()]: "hinted", [b.join()]: "hinted" });
  say(`Try swapping row ${a[0]} column ${a[1]} with row ${b[0]} column ${b[1]}.`);
});

autoBtn.addEventListener("click", () => {
  if (autoplay) {
    autoplay = false;
    showStats();
  } else {
    runAgent();
  }
});

newBtn.addEventListener("click", () => newGame());

async function boot() {
  try {
    const pyodide = await loadPyodide();
    pyodide.FS.mkdirTree("/app/candycrush");
    for (const [dest, url] of Object.entries(PY_FILES)) {
      const resp = await fetch(url);
      if (!resp.ok) throw new Error(`could not load ${url}`);
      pyodide.FS.writeFile(`/app/${dest}`, await resp.text());
    }
    pyodide.runPython("import sys; sys.path.insert(0, '/app')");
    bridge = pyodide.pyimport("bridge");
    newBtn.disabled = false;
    newGame(seedFromUrl());
  } catch (err) {
    say(`Could not start the game: ${err.message}`);
    console.error(err);
  }
}

boot();
