"""Match-3 (Candy Crush style) game for the terminal."""

from .board import Board
from .game import Game, MoveResult, wave_points

__all__ = ["Board", "Game", "MoveResult", "wave_points"]
__version__ = "1.0.0"
