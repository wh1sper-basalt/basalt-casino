"""Game outcome resolution and win calculation from GAME_LIST."""

from __future__ import annotations

from typing import List, Union

from bot.core.games import GAME_LIST
from bot.templates.texts import get_text


def get_game_info(game_id: int, lang: str = "en") -> dict:
    """Return game info with translated names and outcomes."""
    if game_id not in GAME_LIST:
        raise KeyError(f"Unknown game_id: {game_id}")

    game = GAME_LIST[game_id]

    # Get translated name
    name_key = game.get("name_key", f"game_name_{game_id}")
    name = get_text(name_key, lang)

    # Get translated outcomes
    outcome_keys = game.get("outcome_keys", [])
    outcomes = [get_text(key, lang) for key in outcome_keys]

    # Create result with translations
    return {
        "name": name,
        "outcomes": outcomes,
        "ratios": game["ratios"],
        "win_outcome_value": game["win_outcome_value"],
        "all_outcomes_num": game["all_outcomes_num"],
    }


def get_probability(game_id: int, outcome_index: int) -> float:
    """Return probability of outcome (0..1) from all_outcomes_num and win_outcome_value."""
    info = get_game_info(game_id)
    total = info.get("all_outcomes_num") or 6
    wov = info.get("win_outcome_value")
    if not wov or outcome_index >= len(wov):
        return 0.0
    vals = wov[outcome_index]
    if vals is None:
        # Game 1: three outcomes from 2 dice -> 1/3 each roughly (6+6=36, draw=6, win1=15, win2=15)
        return 1.0 / 3.0
    if isinstance(vals, list):
        favorable = len(vals)
    else:
        favorable = 1
    raw = favorable / total if total else 0.0
    return min(1.0, raw)  # cap in case all_outcomes_num is inconsistent with win_outcome_value


def resolve_outcome(
    game_id: int,
    chosen_outcome_index: int,
    dice_values: Union[int, List[int]],
) -> tuple[bool, str, float]:
    """
    Determine win from dice result. Returns (is_win, outcome_name, ratio).
    outcome_name is the actual outcome that occurred; ratio is for the chosen outcome (for payout).
    """
    info = get_game_info(game_id)
    outcomes = info["outcomes"]
    ratios = info["ratios"]
    wov = info.get("win_outcome_value") or []

    if chosen_outcome_index < 0 or chosen_outcome_index >= len(ratios):
        return False, "", 0.0
    ratio = float(ratios[chosen_outcome_index])

    # Game 1: two dice, compare
    if game_id == 1:
        if isinstance(dice_values, list) and len(dice_values) >= 2:
            v1, v2 = int(dice_values[0]), int(dice_values[1])
        else:
            return False, outcomes[chosen_outcome_index], ratio
        if v1 > v2:
            actual_index = 0  # Victory 1
        elif v2 > v1:
            actual_index = 1  # Victory 2
        else:
            actual_index = 2  # Draw
        outcome_name = outcomes[actual_index]
        is_win = actual_index == chosen_outcome_index
        return is_win, outcome_name, ratio

    # Other games: single dice value
    if isinstance(dice_values, list):
        value = int(dice_values[0]) if dice_values else 0
    else:
        value = int(dice_values)
    actual_index = -1
    for i, vals in enumerate(wov):
        if vals is None:
            continue
        if isinstance(vals, list):
            if value in vals:
                actual_index = i
                break
        else:
            if value == vals:
                actual_index = i
                break
    if actual_index < 0:
        outcome_name = outcomes[0]  # fallback
        is_win = False
    else:
        outcome_name = outcomes[actual_index]
        is_win = actual_index == chosen_outcome_index
    return is_win, outcome_name, ratio


def calculate_win_amount(bet_amount: int, ratio: float) -> int:
    """Round bet_amount * ratio to integer."""
    return int(round(bet_amount * ratio))
