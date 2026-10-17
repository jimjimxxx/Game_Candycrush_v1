"""Monte Carlo comparison of the automatic players.

Every agent plays the same set of seeded games, so differences between agents are
compared game by game (paired), which removes the variation that comes from the
starting board.

    python -m candycrush.simulate --games 2000
"""

from __future__ import annotations

import argparse
import csv
import math
import statistics
from typing import Callable, Dict, List

from .agents import GreedyAgent, RandomAgent
from .game import Game

AGENTS: Dict[str, Callable[[int], object]] = {
    "random": lambda s: RandomAgent(seed=s),
    "greedy": lambda s: GreedyAgent(seed=s),
    "greedy-low": lambda s: GreedyAgent(seed=s, prefer_low=True),
}


def play_games(make_agent, games: int, seed: int, **game_kwargs) -> List[int]:
    scores = []
    for i in range(games):
        game = Game(seed=seed + i, **game_kwargs)
        agent = make_agent(seed + i)
        while not game.over:
            game.play_move(agent.choose(game.board))
        scores.append(game.score)
    return scores


def mean_ci(values: List[float], z: float = 1.96):
    m = statistics.fmean(values)
    half = z * statistics.stdev(values) / math.sqrt(len(values))
    return m, m - half, m + half


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--games", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--rows", type=int, default=8)
    parser.add_argument("--cols", type=int, default=8)
    parser.add_argument("--types", type=int, default=5)
    parser.add_argument("--moves", type=int, default=15)
    parser.add_argument("--csv", help="write per-game scores to this file")
    args = parser.parse_args(argv)

    kwargs = dict(rows=args.rows, cols=args.cols, n_types=args.types, moves=args.moves)
    scores = {name: play_games(make, args.games, args.seed, **kwargs) for name, make in AGENTS.items()}

    print(f"{args.games} games per agent, {args.rows}x{args.cols} board, {args.types} types, {args.moves} moves\n")
    print("| agent | mean score | 95% CI | sd | median |")
    print("|---|---|---|---|---|")
    for name, s in scores.items():
        m, lo, hi = mean_ci(s)
        print(f"| {name} | {m:.1f} | [{lo:.1f}, {hi:.1f}] | {statistics.stdev(s):.1f} | {statistics.median(s):.0f} |")

    print("\nPaired differences (same seeds):\n")
    print("| comparison | mean difference | 95% CI |")
    print("|---|---|---|")
    for a, b in (("greedy", "random"), ("greedy-low", "greedy")):
        m, lo, hi = mean_ci([x - y for x, y in zip(scores[a], scores[b])])
        print(f"| {a} - {b} | {m:+.1f} | [{lo:+.1f}, {hi:+.1f}] |")

    if args.csv:
        with open(args.csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["game", *scores])
            for i, row in enumerate(zip(*scores.values())):
                writer.writerow([i, *row])


if __name__ == "__main__":
    main()
