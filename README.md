# Game_Candycrush_v1

**Play in the browser: https://jimjimxxx.github.io/Game_Candycrush_v1/**

A match-3 (Candy Crush style) game for the terminal and the browser. This is a rewrite of my 2024 version, [Game_Candycrush](https://github.com/jimjimxxx/early-projects/tree/main/Game_Candycrush): the rules engine is separated from the interface, covered by tests, and used by simple automatic players to compare strategies with a Monte Carlo simulation.

```
Score 0   Moves left 15

  0 1 2 3 4 5 6 7
0 Y P R G R B B P
1 B Y R B R B B R
2 B G G R B R R Y
3 R B Y B R P Y B
4 B P Y G Y Y P G
5 R B R Y G R G P
6 B P Y G G P P B
7 P R B Y P B Y G

> 1 3 r
Cleared 3 + 3 candies, +6 points
```

(`--seed 1`; the second 3 is a cascade.)

## Quick start

Python 3.9+ with no third-party dependencies (pytest only for the tests).

```bash
python -m candycrush                  # play
python -m candycrush --seed 1         # same board every time
python -m candycrush --rows 6 --cols 9 --types 6 --moves 20
python -m pytest                      # run the tests
python -m candycrush.simulate         # compare the automatic players
```

Moves are typed as `r1 c1 r2 c2` (e.g. `3 4 3 5`) or `r c dir` with `dir` in `u/d/l/r` (e.g. `3 4 r`). `h` shows a hint, `q` quits.

## Rules

- 8×8 board, 5 candy types, 15 moves by default.
- Swap two adjacent candies. If this lines up three or more of the same type horizontally or vertically, they are cleared, the candies above fall down, new candies drop in from the top, and any new lines are cleared as well (cascades).
- A swap that makes no line is undone but still costs a move. Mistyped coordinates (out of bounds, not adjacent) do not.
- Each clearing wave scores *candies cleared × multiplier*: 3–6 candies ×1, 7–12 ×2, 13 or more ×5.
- A new board never starts with a ready-made line and always has at least one possible move. If the board runs out of moves, it is reshuffled.

## Code structure

| File | Contents |
|---|---|
| `candycrush/board.py` | Board state, match detection, gravity and refill, valid-move search |
| `candycrush/game.py` | Move handling, cascades, scoring, reshuffles |
| `candycrush/agents.py` | Random and greedy automatic players |
| `candycrush/simulate.py` | Monte Carlo comparison of the players |
| `candycrush/cli.py` | Terminal interface and input parsing |
| `web/` | Browser version: page, styles, and a small bridge to the Python package |
| `tests/` | pytest suite (235 cases, including 200 seeded boards) |
| `.github/workflows/pages.yml` | Runs the tests on every push, then publishes the browser version |

All randomness goes through a seeded `random.Random`, so any game can be replayed exactly; `--seed 1` in the terminal and `?seed=1` in the browser give the same game.

## Browser version

The web page does not reimplement the rules in JavaScript. It loads [Pyodide](https://pyodide.org) (CPython compiled to WebAssembly) and imports the same `candycrush` package, so the code the tests cover is the code the browser runs. JavaScript only draws the board and handles clicks and swipes; `Game.play(..., record=True)` returns the board before each cascade wave so the page can animate it. The "Let the greedy agent play" button runs the greedy player from `agents.py`.

GitHub Actions runs pytest on each push to `main`; if the tests pass, it copies `web/` and the package into a static site and deploys it to GitHub Pages. The first visit takes a few seconds while Pyodide downloads.

## What changed from the 2024 version

The original was one 266-line script. Besides restructuring it, the rewrite fixes these problems:

- **Stuck boards caused an infinite loop.** When no move was possible, a new board was created inside a helper but only assigned to a local variable. The game kept the old board, which still had no moves, so the main loop never ended.
- **Free points before the first move.** Random starting boards could already contain lines, which were cleared and scored before the player did anything. Boards are now generated without lines.
- **One move was lost.** The loop condition `while eliminate_numbers > 1` allowed 14 of the 15 moves.
- **Crashes on bad input.** Coordinates were read with `int(input())`, so any non-number crashed the game, and a board size of 0 was accepted. Input is now validated.
- **Error messages printed twice.** An invalid swap was checked twice in a row.
- **Dead code.** The loop meant to extend runs longer than three, `range(cols + 3, cols)`, never ran. Long runs were still detected through overlapping triples. The new version finds runs with a single run-length scan.

## Strategy comparison

Three automatic players:

- **random**: picks any valid move.
- **greedy**: picks the move that scores the most in its first wave. It cannot see cascades, because they depend on random refills.
- **greedy-low**: same as greedy, but breaks ties in favour of the move nearest the bottom of the board.

Each player plays the same 2,000 seeded games. Because the games share seeds, the players are compared game by game (paired differences), which removes the variation that comes from the starting board. Intervals are normal-approximation 95% confidence intervals.

```bash
python -m candycrush.simulate --games 2000 --seed 0
```

| agent | mean score | 95% CI | sd | median |
|---|---|---|---|---|
| random | 106.9 | [105.5, 108.4] | 33.1 | 100 |
| greedy | 147.1 | [145.2, 149.1] | 44.3 | 140 |
| greedy-low | 157.0 | [155.1, 159.0] | 45.4 | 149 |

| comparison | mean difference | 95% CI |
|---|---|---|
| greedy − random | +40.2 | [+37.9, +42.5] |
| greedy-low − greedy | +9.9 | [+7.7, +12.1] |

Playing greedily raises the average score by about 38%. Preferring low moves adds about 10 more points. A plausible reason is that clearing near the bottom makes more candies fall, which gives more chances for cascades; the simulation shows the effect but does not isolate the cause. The run takes about 1.5 minutes.

## Possible extensions

- Special candies (striped, wrapped) for runs of 4 and 5
- A lookahead player that estimates cascade value by sampling refills
- Smoother animation of candies falling into place in the browser version
