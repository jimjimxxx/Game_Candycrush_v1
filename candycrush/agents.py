"""Simple automatic players, used for testing the rules and comparing strategies."""

from __future__ import annotations

import random
from typing import Optional

from .board import Board, Move
from .game import wave_points


class RandomAgent:
    """Plays a uniformly random valid move."""

    name = "random"

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)

    def choose(self, board: Board) -> Move:
        return self.rng.choice(board.valid_moves())


class GreedyAgent:
    """Plays the move that scores the most in its first wave.

    It only looks at what the swap itself clears; cascades depend on random refills,
    which the agent cannot see. With prefer_low=True, ties go to the move closest to
    the bottom of the board, since clearing low disturbs more candies above it.
    """

    def __init__(self, seed: Optional[int] = None, prefer_low: bool = False):
        self.rng = random.Random(seed)
        self.prefer_low = prefer_low
        self.name = "greedy-low" if prefer_low else "greedy"

    def choose(self, board: Board) -> Move:
        best, best_key = [], None
        for move in board.valid_moves():
            points = wave_points(len(board.swap_result(move)))
            depth = max(move[0][0], move[1][0]) if self.prefer_low else 0
            key = (points, depth)
            if best_key is None or key > best_key:
                best, best_key = [move], key
            elif key == best_key:
                best.append(move)
        return self.rng.choice(best)
