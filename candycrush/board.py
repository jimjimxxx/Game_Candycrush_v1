"""Board state and match-3 mechanics."""

from __future__ import annotations

import random
from typing import Iterable, List, Set, Tuple

Cell = Tuple[int, int]
Move = Tuple[Cell, Cell]

EMPTY = 0
MIN_RUN = 3


class Board:
    """A rows x cols grid of candies. Candy types are 1..n_types; 0 marks an empty cell."""

    def __init__(self, grid: List[List[int]], n_types: int):
        if not grid or not grid[0]:
            raise ValueError("grid must be non-empty")
        width = len(grid[0])
        if any(len(row) != width for row in grid):
            raise ValueError("grid rows must all have the same length")
        self.grid = [list(row) for row in grid]
        self.rows = len(grid)
        self.cols = width
        self.n_types = n_types

    # ------------------------------------------------------------------ creation

    @classmethod
    def random(cls, rows: int, cols: int, n_types: int, rng: random.Random) -> "Board":
        """Random board with no ready-made matches and at least one valid move."""
        if rows < MIN_RUN or cols < MIN_RUN:
            raise ValueError(f"board must be at least {MIN_RUN}x{MIN_RUN}")
        if n_types < 3:
            raise ValueError("need at least 3 candy types")
        while True:
            grid = [[EMPTY] * cols for _ in range(rows)]
            for r in range(rows):
                for c in range(cols):
                    banned = set()
                    if c >= 2 and grid[r][c - 1] == grid[r][c - 2]:
                        banned.add(grid[r][c - 1])
                    if r >= 2 and grid[r - 1][c] == grid[r - 2][c]:
                        banned.add(grid[r - 1][c])
                    grid[r][c] = rng.choice([t for t in range(1, n_types + 1) if t not in banned])
            board = cls(grid, n_types)
            if board.has_valid_move():
                return board

    def copy(self) -> "Board":
        return Board(self.grid, self.n_types)

    # ------------------------------------------------------------------ queries

    def in_bounds(self, cell: Cell) -> bool:
        r, c = cell
        return 0 <= r < self.rows and 0 <= c < self.cols

    @staticmethod
    def are_adjacent(a: Cell, b: Cell) -> bool:
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1

    def _run(self, r: int, c: int, dr: int, dc: int) -> List[Cell]:
        """Cells in the straight run through (r, c) along (dr, dc) that share its type."""
        kind = self.grid[r][c]
        if kind == EMPTY:
            return []
        cells = [(r, c)]
        for sign in (1, -1):
            rr, cc = r + sign * dr, c + sign * dc
            while 0 <= rr < self.rows and 0 <= cc < self.cols and self.grid[rr][cc] == kind:
                cells.append((rr, cc))
                rr, cc = rr + sign * dr, cc + sign * dc
        return cells

    def matches_through(self, cells: Iterable[Cell]) -> Set[Cell]:
        """Matched cells on any horizontal or vertical run of 3+ that passes through `cells`."""
        matched: Set[Cell] = set()
        for r, c in cells:
            for dr, dc in ((0, 1), (1, 0)):
                run = self._run(r, c, dr, dc)
                if len(run) >= MIN_RUN:
                    matched.update(run)
        return matched

    def find_matches(self) -> Set[Cell]:
        """All cells that belong to a horizontal or vertical run of 3 or more."""
        matched: Set[Cell] = set()
        for r in range(self.rows):
            matched.update(self._scan_line([(r, c) for c in range(self.cols)]))
        for c in range(self.cols):
            matched.update(self._scan_line([(r, c) for r in range(self.rows)]))
        return matched

    def _scan_line(self, line: List[Cell]) -> Set[Cell]:
        matched: Set[Cell] = set()
        start = 0
        for i in range(1, len(line) + 1):
            same = i < len(line) and self.grid[line[i][0]][line[i][1]] == self.grid[line[start][0]][line[start][1]]
            if not same:
                kind = self.grid[line[start][0]][line[start][1]]
                if kind != EMPTY and i - start >= MIN_RUN:
                    matched.update(line[start:i])
                start = i
        return matched

    def swap_result(self, move: Move) -> Set[Cell]:
        """Cells the swap would clear in its first wave (empty set means the swap is not valid).

        Assumes the board currently has no matches, which holds between moves.
        """
        a, b = move
        self.swap(a, b)
        try:
            return self.matches_through((a, b))
        finally:
            self.swap(a, b)

    def valid_moves(self) -> List[Move]:
        moves = []
        for r in range(self.rows):
            for c in range(self.cols):
                for nb in ((r, c + 1), (r + 1, c)):
                    if self.in_bounds(nb) and self.grid[r][c] != self.grid[nb[0]][nb[1]]:
                        if self.swap_result(((r, c), nb)):
                            moves.append(((r, c), nb))
        return moves

    def has_valid_move(self) -> bool:
        return bool(self.valid_moves())

    # ------------------------------------------------------------------ mutation

    def swap(self, a: Cell, b: Cell) -> None:
        (r1, c1), (r2, c2) = a, b
        self.grid[r1][c1], self.grid[r2][c2] = self.grid[r2][c2], self.grid[r1][c1]

    def clear(self, cells: Iterable[Cell]) -> None:
        for r, c in cells:
            self.grid[r][c] = EMPTY

    def collapse(self) -> None:
        """Let candies fall into empty cells below them."""
        for c in range(self.cols):
            column = [self.grid[r][c] for r in range(self.rows) if self.grid[r][c] != EMPTY]
            column = [EMPTY] * (self.rows - len(column)) + column
            for r in range(self.rows):
                self.grid[r][c] = column[r]

    def refill(self, rng: random.Random) -> None:
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == EMPTY:
                    self.grid[r][c] = rng.randint(1, self.n_types)

    def __str__(self) -> str:
        return "\n".join(" ".join(str(v) for v in row) for row in self.grid)
