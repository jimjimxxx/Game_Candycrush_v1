import random

import pytest

from candycrush.board import EMPTY, Board


def make(rows):
    return Board([list(map(int, r.split())) for r in rows], n_types=5)


def test_find_matches_horizontal_and_vertical():
    b = make([
        "1 1 1 2",
        "3 4 5 2",
        "4 5 3 2",
    ])
    assert b.find_matches() == {(0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 3)}


def test_long_run_is_matched_in_full():
    b = make([
        "2 2 2 2 2",
        "1 3 1 3 1",
        "3 1 3 1 3",
    ])
    assert b.find_matches() == {(0, c) for c in range(5)}


def test_no_match_for_runs_of_two():
    b = make([
        "1 1 2",
        "2 2 1",
        "1 1 2",
    ])
    assert b.find_matches() == set()


def test_matches_through_agrees_with_full_scan_after_a_swap():
    b = make([
        "1 2 1 1",
        "3 1 4 5",
        "4 5 3 2",
    ])
    move = ((0, 1), (1, 1))
    cleared = b.swap_result(move)
    assert cleared == {(0, 0), (0, 1), (0, 2), (0, 3)}
    assert b.grid[0][1] == 2  # swap_result leaves the board unchanged
    b.swap(*move)
    assert b.find_matches() == cleared


def test_valid_moves_finds_the_only_move():
    b = make([
        "1 2 1",
        "3 1 4",
        "4 5 3",
    ])
    assert b.valid_moves() == [((0, 1), (1, 1))]


def test_collapse_drops_candies_and_keeps_order():
    b = make([
        "1 2",
        "3 4",
        "5 1",
    ])
    b.clear([(2, 0), (1, 1)])
    b.collapse()
    assert b.grid == [[EMPTY, EMPTY], [1, 2], [3, 1]]


def test_refill_leaves_no_empty_cells():
    b = make(["1 2 3", "1 2 3", "2 3 1"])
    b.clear([(0, 0), (1, 1)])
    b.collapse()
    b.refill(random.Random(0))
    assert all(v != EMPTY for row in b.grid for v in row)


@pytest.mark.parametrize("seed", range(200))
def test_random_board_has_no_matches_and_a_valid_move(seed):
    b = Board.random(8, 8, 5, random.Random(seed))
    assert b.find_matches() == set()
    assert b.has_valid_move()


def test_rejects_bad_sizes():
    with pytest.raises(ValueError):
        Board.random(2, 8, 5, random.Random(0))
    with pytest.raises(ValueError):
        Board.random(8, 8, 2, random.Random(0))
    with pytest.raises(ValueError):
        Board([[1, 2], [3]], n_types=5)
