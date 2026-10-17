"""Game rules: moves, cascades, scoring and reshuffles."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple

from .board import Board, Cell, Move


def wave_points(cleared: int) -> int:
    """Points for one clearing wave: 3-6 candies x1, 7-12 candies x2, 13+ candies x5."""
    if cleared < 3:
        return 0
    if cleared <= 6:
        multiplier = 1
    elif cleared <= 12:
        multiplier = 2
    else:
        multiplier = 5
    return cleared * multiplier


@dataclass
class MoveResult:
    valid: bool
    waves: List[int] = field(default_factory=list)  # candies cleared in each cascade wave
    points: int = 0
    reshuffled: bool = False
    # With record=True: the board just before each wave is cleared, and the cells it clears.
    steps: List[Tuple[List[List[int]], Set[Cell]]] = field(default_factory=list)


class Game:
    """One game: a fixed number of moves on a random board.

    A swap of two adjacent candies that does not create a match is undone but still
    uses up a move (the rule from the original version). Coordinates that are out of
    bounds or not adjacent raise ValueError and do not use a move.
    """

    def __init__(
        self,
        rows: int = 8,
        cols: int = 8,
        n_types: int = 5,
        moves: int = 15,
        seed: Optional[int] = None,
    ):
        if moves < 1:
            raise ValueError("moves must be positive")
        self.rng = random.Random(seed)
        self.board = Board.random(rows, cols, n_types, self.rng)
        self.moves_left = moves
        self.score = 0

    @property
    def over(self) -> bool:
        return self.moves_left == 0

    def play(self, a: Cell, b: Cell, record: bool = False) -> MoveResult:
        if self.over:
            raise RuntimeError("game is over")
        if not (self.board.in_bounds(a) and self.board.in_bounds(b)):
            raise ValueError("cell out of bounds")
        if not Board.are_adjacent(a, b):
            raise ValueError("cells are not adjacent")

        self.moves_left -= 1
        if not self.board.swap_result((a, b)):
            return MoveResult(valid=False)

        self.board.swap(a, b)
        result = MoveResult(valid=True)
        matched = self.board.matches_through((a, b))
        while matched:
            if record:
                result.steps.append(([row[:] for row in self.board.grid], set(matched)))
            result.waves.append(len(matched))
            result.points += wave_points(len(matched))
            self.board.clear(matched)
            self.board.collapse()
            self.board.refill(self.rng)
            matched = self.board.find_matches()

        if not self.board.has_valid_move():
            board = self.board
            self.board = Board.random(board.rows, board.cols, board.n_types, self.rng)
            result.reshuffled = True

        self.score += result.points
        return result

    def play_move(self, move: Move, record: bool = False) -> MoveResult:
        return self.play(*move, record=record)
