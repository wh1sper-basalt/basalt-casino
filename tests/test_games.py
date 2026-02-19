"""Tests for game logic: get_game_info, resolve_outcome, probability, win calculation."""

from __future__ import annotations

import pytest

from bot.services.game import calculate_win_amount, get_game_info, get_probability, resolve_outcome


def test_get_game_info() -> None:
    """get_game_info returns GAME_LIST entry with translated names."""
    info = get_game_info(1, lang="en")
    assert info["name"] == "🎲 2 Dices"
    assert info["outcomes"] == ["Victory 1", "Victory 2", "Draw"]
    assert info["ratios"] == [1.8, 1.8, 1.8]


def test_get_game_info_unknown_raises() -> None:
    """get_game_info with unknown game_id raises KeyError."""
    with pytest.raises(KeyError):
        get_game_info(999)


def test_calculate_win_amount() -> None:
    """calculate_win_amount returns bet * ratio rounded."""
    assert calculate_win_amount(100, 1.8) == 180
    assert calculate_win_amount(50, 2.5) == 125


@pytest.mark.parametrize(
    "game_id,outcome_index,dice_values,expected_win,expected_outcome_name",
    [
        (2, 0, 5, True, "More"),  # English outcomes
        (2, 0, 3, False, "Less"),
        (2, 1, 1, True, "Less"),
        (3, 0, 2, True, "Even"),
        (3, 1, 3, True, "Odd"),
        (3, 0, 1, False, "Odd"),
    ],
)
def test_resolve_outcome_single_dice(
    game_id: int,
    outcome_index: int,
    dice_values: int | list[int],
    expected_win: bool,
    expected_outcome_name: str,
) -> None:
    """resolve_outcome for single-dice games: win and outcome name match win_outcome_value."""
    is_win, outcome_name, ratio = resolve_outcome(game_id, outcome_index, dice_values)
    assert is_win is expected_win
    assert outcome_name == expected_outcome_name
    assert ratio == 1.8


def test_resolve_outcome_game1_two_dice() -> None:
    """Game 1 (two dice): compare values; win when chosen outcome matches (Victory 1, Victory 2, Draw)."""
    # Victory 1 = first > second -> index 0
    is_win, name, ratio = resolve_outcome(1, 0, [5, 3])
    assert is_win is True
    assert name == "Victory 1"
    assert ratio == 1.8

    # Victory 2 = second > first -> index 1
    is_win, name, ratio = resolve_outcome(1, 1, [2, 4])
    assert is_win is True
    assert name == "Victory 2"
    assert ratio == 1.8

    # Draw = equal -> index 2
    is_win, name, ratio = resolve_outcome(1, 2, [3, 3])
    assert is_win is True
    assert name == "Draw"
    assert ratio == 1.8

    # Wrong choice -> lose
    is_win, name, ratio = resolve_outcome(1, 0, [2, 5])
    assert is_win is False
    assert name == "Victory 2"
    assert ratio == 1.8


def test_get_probability() -> None:
    """get_probability returns correct probability based on win_outcome_value."""
    # Game 2: More (outcome 0) has 3 favorable values (4,5,6) out of 6 → 0.5
    assert get_probability(2, 0) == 0.5
    # Game 2: Less (outcome 1) also 3/6 → 0.5
    assert get_probability(2, 1) == 0.5
    # Game 3: Even (2,4,6) → 0.5
    assert get_probability(3, 0) == 0.5
    # Game 3: Odd (1,3,5) → 0.5
    assert get_probability(3, 1) == 0.5
    # Game 1: special case → 1/3
    assert get_probability(1, 0) == 1 / 3
