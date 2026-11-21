from unittest.mock import patch

import pandas as pd
import pytest

from src.tools.pybaseball_tools import retrieve_advanced_hitting_stats


@pytest.mark.parametrize("expected_woba", [0.0, None])
def test_advanced_hitting_stats_uses_requested_player_and_season(expected_woba):
    leaderboard = pd.DataFrame(
        [
            {"player_id": 1, "year": 2025, "pa": 100, "woba": 0.400, "est_woba": 0.410},
            {"player_id": 2, "year": 2024, "pa": 200, "woba": 0.390, "est_woba": 0.385},
            {"player_id": 2, "year": 2025, "pa": 1, "woba": 0.0, "est_woba": expected_woba},
        ]
    )
    with patch("src.tools.pybaseball_tools.statcast_batter_expected_stats", return_value=leaderboard) as fetch:
        result = retrieve_advanced_hitting_stats.invoke({"mlbam_id": 2, "season": 2025})

    fetch.assert_called_once_with(2025, minPA=1)
    assert result == {
        "mlbam_id": 2,
        "season": 2025,
        "source": "Baseball Savant",
        "plate_appearances": 1,
        "woba": 0.0,
        "xwoba": expected_woba,
    }


def test_advanced_hitting_stats_reports_absent_player():
    leaderboard = pd.DataFrame([{"player_id": 1, "year": 2025}])
    with patch("src.tools.pybaseball_tools.statcast_batter_expected_stats", return_value=leaderboard):
        result = retrieve_advanced_hitting_stats.invoke({"mlbam_id": 2, "season": 2025})

    assert "error" in result
    assert "woba" not in result
