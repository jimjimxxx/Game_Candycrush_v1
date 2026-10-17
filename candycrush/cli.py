"""Terminal front end."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Optional

from .board import Board, Move
from .game import Game

SYMBOLS = "RYGBPCWO"
COLORS = ["91", "93", "92", "94", "95", "96", "97", "33"]

DIRECTIONS = {"u": (-1, 0), "d": (1, 0), "l": (0, -1), "r": (0, 1)}

HELP = """Enter a move as either
  r1 c1 r2 c2   swap two adjacent cells, e.g. "3 4 3 5"
  r c dir       swap a cell with its neighbour, dir is u/d/l/r, e.g. "3 4 r"
Other commands: h = hint, ? = help, q = quit."""


def parse_move(text: str) -> Move:
    """Parse a move typed by the player. Raises ValueError with a readable message."""
    parts = text.replace(",", " ").lower().split()
    if len(parts) == 3 and parts[2] in DIRECTIONS:
        if not (parts[0].isdigit() and parts[1].isdigit()):
            raise ValueError("row and column must be non-negative integers")
        r, c = int(parts[0]), int(parts[1])
        dr, dc = DIRECTIONS[parts[2]]
        return (r, c), (r + dr, c + dc)
    if len(parts) == 4:
        if not all(p.isdigit() for p in parts):
            raise ValueError("row and column must be non-negative integers")
        r1, c1, r2, c2 = map(int, parts)
        return (r1, c1), (r2, c2)
    raise ValueError('could not read that move, type "?" for help')


def render(board: Board, color: bool) -> str:
    def cell(v: int) -> str:
        if v > len(SYMBOLS):
            return str(v)
        s = SYMBOLS[v - 1]
        return f"\033[{COLORS[v - 1]}m{s}\033[0m" if color else s

    width = len(str(board.rows - 1))
    lines = [" " * (width + 1) + " ".join(f"{c}" for c in range(board.cols))]
    for r, row in enumerate(board.grid):
        lines.append(f"{r:>{width}} " + " ".join(cell(v) for v in row))
    return "\n".join(lines)


def main(argv: Optional[list] = None) -> None:
    parser = argparse.ArgumentParser(description="Match-3 game in the terminal.")
    parser.add_argument("--rows", type=int, default=8)
    parser.add_argument("--cols", type=int, default=8)
    parser.add_argument("--types", type=int, default=5, help="number of candy types (3-8)")
    parser.add_argument("--moves", type=int, default=15)
    parser.add_argument("--seed", type=int, default=None, help="fix the random seed")
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args(argv)
    if not 3 <= args.types <= len(SYMBOLS):
        parser.error(f"--types must be between 3 and {len(SYMBOLS)}")

    color = not args.no_color and sys.stdout.isatty()
    if color and os.name == "nt":
        os.system("")  # turns on ANSI colour handling in the Windows console

    try:
        game = Game(args.rows, args.cols, args.types, args.moves, seed=args.seed)
    except ValueError as e:
        parser.error(str(e))

    print(HELP)
    try:
        while not game.over:
            print(f"\nScore {game.score}   Moves left {game.moves_left}\n")
            print(render(game.board, color))
            text = input("\n> ").strip().lower()
            if text in ("q", "quit"):
                break
            if text in ("?", "help"):
                print(HELP)
                continue
            if text in ("h", "hint"):
                (r1, c1), (r2, c2) = game.board.valid_moves()[0]
                print(f"Try {r1} {c1} {r2} {c2}")
                continue
            try:
                result = game.play_move(parse_move(text))
            except ValueError as e:
                print(f"Invalid input: {e}")
                continue
            if not result.valid:
                print("No match, swap undone. That still used a move.")
            else:
                waves = " + ".join(str(n) for n in result.waves)
                print(f"Cleared {waves} candies, +{result.points} points")
            if result.reshuffled:
                print("No moves left on the board, reshuffled.")
    except (EOFError, KeyboardInterrupt):
        print()
    print(f"\nGame over. Final score: {game.score}")


if __name__ == "__main__":
    main()
