"""GAME_LIST: game id -> name, outcomes, ratios, win_outcome_value, all_outcomes_num. Telegram emoji type mapping."""

from __future__ import annotations

from typing import Dict, List, Optional, Union

# Game id (1-8) -> config. Coefficients can be overridden from DB (settings).
# Values: name (str), outcomes (list[str]), ratios (list[float]), win_outcome_value, all_outcomes_num (int).
GAME_LIST: Dict[int, Dict[str, Union[str, List[str], List[float], Optional[List], int]]] = {
    1: {
        "name_key": "game_name_1",
        "outcome_keys": ["game_outcome_1_0", "game_outcome_1_1", "game_outcome_1_2"],
        "ratios": [1.8, 1.8, 1.8],
        "win_outcome_value": [None],
        "all_outcomes_num": 2,
    },
    2: {
        "name_key": "game_name_2",
        "outcome_keys": ["game_outcome_2_0", "game_outcome_2_1"],
        "ratios": [1.8, 1.8],
        "win_outcome_value": [[4, 5, 6], [1, 2, 3]],
        "all_outcomes_num": 6,
    },
    3: {
        "name_key": "game_name_3",
        "outcome_keys": ["game_outcome_3_0", "game_outcome_3_1"],
        "ratios": [1.8, 1.8],
        "win_outcome_value": [[2, 4, 6], [1, 3, 5]],
        "all_outcomes_num": 6,
    },
    4: {
        "name_key": "game_name_4",
        "outcome_keys": [
            "game_outcome_4_0",
            "game_outcome_4_1",
            "game_outcome_4_2",
            "game_outcome_4_3",
        ],
        "ratios": [1.8, 1.8, 1.8, 1.8],
        "win_outcome_value": [[2, 4, 6], [3, 5], [6], [1]],
        "all_outcomes_num": 6,
    },
    5: {
        "name_key": "game_name_5",
        "outcome_keys": ["game_outcome_5_0", "game_outcome_5_1", "game_outcome_5_2"],
        "ratios": [1.8, 1.8, 1.8],
        "win_outcome_value": [[4, 5], [1, 2], [3]],
        "all_outcomes_num": 5,
    },
    6: {
        "name_key": "game_name_6",
        "outcome_keys": [
            "game_outcome_6_0",
            "game_outcome_6_1",
            "game_outcome_6_2",
            "game_outcome_6_3",
            "game_outcome_6_4",
            "game_outcome_6_5",
        ],
        "ratios": [1.8, 1.8, 1.8, 1.8, 1.8, 1.8],
        "win_outcome_value": [[3, 4, 5], [1, 2], [2, 4], [4], [5], [3]],
        "all_outcomes_num": 5,
    },
    7: {
        "name_key": "game_name_7",
        "outcome_keys": [
            "game_outcome_7_0",
            "game_outcome_7_1",
            "game_outcome_7_2",
            "game_outcome_7_3",
            "game_outcome_7_4",
        ],
        "ratios": [1.8, 1.8, 1.8, 1.8, 1.8],
        "win_outcome_value": [[1], [6], [2, 3, 4, 5, 6], [2, 3], [3, 4, 5, 6]],
        "all_outcomes_num": 6,
    },
    8: {
        "name_key": "game_name_8",
        "outcome_keys": [
            "game_outcome_8_0",
            "game_outcome_8_1",
            "game_outcome_8_2",
            "game_outcome_8_3",
        ],
        "ratios": [1.8, 1.8, 1.8, 1.8],
        "win_outcome_value": [[22], [43], [1], [64]],
        "all_outcomes_num": 64,
    },
}

# game_id -> Telegram dice emoji type
GAME_ID_TO_EMOJI: Dict[int, str] = {
    1: "dice",
    2: "dice",
    3: "dice",
    4: "darts",
    5: "basketball",
    6: "football",
    7: "bowling",
    8: "slot_machine",
}

# game_id -> image screen name (basalt_{screen}_{lang}.png for description, outcomes, amount)
GAME_ID_TO_IMAGE_SCREEN: Dict[int, str] = {
    1: "2dices",
    2: "moreless",
    3: "evenodd",
    4: "dart",
    5: "basketball",
    6: "football",
    7: "bowling",
    8: "slots",
}
