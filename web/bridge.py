"""Glue between the browser page and the candycrush package (runs inside Pyodide)."""

import json

from candycrush import Game
from candycrush.agents import GreedyAgent

_game = None
_agent = None


def new_game(seed=None):
    global _game, _agent
    _game = Game(seed=seed)
    _agent = GreedyAgent(seed=seed)
    return state()


def _state():
    return {
        "grid": _game.board.grid,
        "score": _game.score,
        "moves_left": _game.moves_left,
        "over": _game.over,
    }


def state():
    return json.dumps(_state())


def play(r1, c1, r2, c2):
    try:
        result = _game.play((r1, c1), (r2, c2), record=True)
    except ValueError as e:
        return json.dumps({"error": str(e), **_state()})
    steps = [{"grid": grid, "cleared": sorted(cells)} for grid, cells in result.steps]
    return json.dumps({
        "valid": result.valid,
        "waves": result.waves,
        "points": result.points,
        "reshuffled": result.reshuffled,
        "steps": steps,
        **_state(),
    })


def hint():
    return json.dumps(_agent.choose(_game.board))
