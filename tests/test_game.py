import random

import pytest

from candycrush.agents import GreedyAgent, RandomAgent
from candycrush.board import Board
from candycrush.cli import parse_move
from candycrush.game import Game, wave_points


@pytest.mark.parametrize(
    "cleared, points",
    [(0, 0), (2, 0), (3, 3), (6, 6), (7, 14), (12, 24), (13, 65)],
)
def test_wave_points(cleared, points):
    assert wave_points(cleared) == points


def game_with(rows, seed=0, moves=15):
    g = Game(seed=seed, moves=moves)
    g.board = Board([list(map(int, r.split())) for r in rows], n_types=5)
    return g


def test_valid_move_scores_and_uses_a_move():
    g = game_with([
        "1 2 1 1",
        "3 1 4 5",
        "4 5 3 2",
    ])
    result = g.play((0, 1), (1, 1))
    assert result.valid
    assert result.waves[0] == 4
    assert g.score == result.points >= 4
    assert g.moves_left == 14
    assert g.board.find_matches() == set()


def test_record_keeps_one_step_per_wave():
    g = game_with([
        "1 2 1 1",
        "3 1 4 5",
        "4 5 3 2",
    ])
    result = g.play((0, 1), (1, 1), record=True)
    assert len(result.steps) == len(result.waves)
    grid, cleared = result.steps[0]
    assert cleared == {(0, 0), (0, 1), (0, 2), (0, 3)}
    assert grid[0] == [1, 1, 1, 1]  # board after the swap, before clearing
    assert [len(c) for _, c in result.steps] == result.waves


def test_swap_without_match_is_undone_but_uses_a_move():
    g = game_with([
        "1 2 1 1",
        "3 1 4 5",
        "4 5 3 2",
    ])
    before = [row[:] for row in g.board.grid]
    result = g.play((2, 0), (2, 1))
    assert not result.valid
    assert g.board.grid == before
    assert g.moves_left == 14
    assert g.score == 0


@pytest.mark.parametrize("move", [((0, 0), (0, 2)), ((0, 0), (1, 1)), ((0, 0), (-1, 0)), ((7, 7), (7, 8))])
def test_bad_coordinates_raise_and_do_not_use_a_move(move):
    g = Game(seed=1)
    with pytest.raises(ValueError):
        g.play(*move)
    assert g.moves_left == 15


def test_game_ends_after_the_last_move():
    g = Game(seed=3, moves=2)
    agent = RandomAgent(seed=3)
    g.play_move(agent.choose(g.board))
    g.play_move(agent.choose(g.board))
    assert g.over
    with pytest.raises(RuntimeError):
        g.play_move(((0, 0), (0, 1)))


def play_out(seed, agent):
    g = Game(seed=seed)
    while not g.over:
        g.play_move(agent.choose(g.board))
    return g.score


def test_same_seed_gives_the_same_game():
    assert play_out(42, RandomAgent(seed=42)) == play_out(42, RandomAgent(seed=42))


def test_board_always_has_a_move_between_turns():
    g = Game(seed=7, moves=200, n_types=6)
    agent = RandomAgent(seed=7)
    while not g.over:
        assert g.board.find_matches() == set()
        assert g.board.has_valid_move()
        g.play_move(agent.choose(g.board))


def test_greedy_picks_the_largest_first_wave():
    b = Board([list(map(int, r.split())) for r in [
        "1 2 1 1 3",
        "4 1 5 2 2",
        "3 4 3 2 4",
        "5 3 4 1 5",
    ]], n_types=5)
    best = max(len(b.swap_result(m)) for m in b.valid_moves())
    move = GreedyAgent(seed=0).choose(b)
    assert len(b.swap_result(move)) == best == 4


@pytest.mark.parametrize(
    "text, move",
    [("3 4 3 5", ((3, 4), (3, 5))), ("3,4 r", ((3, 4), (3, 5))), ("0 0 d", ((0, 0), (1, 0))), (" 2 2 U ", ((2, 2), (1, 2)))],
)
def test_parse_move(text, move):
    assert parse_move(text) == move


@pytest.mark.parametrize("text", ["", "3 4", "a b c d", "3 4 x", "-1 0 0 0"])
def test_parse_move_rejects_garbage(text):
    with pytest.raises(ValueError):
        parse_move(text)
