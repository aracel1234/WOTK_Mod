from __future__ import annotations

from wotk.automation.windowing import WindowRect
from wotk.features.multi_instance import InstanceConfig, MultiInstanceMaster
from wotk.models import Point


def test_window_rect_relative_transform():
    rect = WindowRect(100, 200, 800, 600)
    assert rect.absolute(Point(10, 20), Point(2, -3)) == Point(112, 217)


def test_master_config_parse():
    cfg = MultiInstanceMaster.from_dict(
        {
            "sandboxie_settings": {"sandboxie_path": "Start.exe", "max_instances": 3},
            "global_settings": {"base_delay": 0.5, "max_retries": 2},
            "threading_config": {"thread_pool_size": 3},
        }
    )
    assert cfg.max_instances == 3
    assert cfg.thread_pool_size == 3


def test_instance_config_parse_point_lists():
    data = {
        "instance_info": {
            "instance_id": 1,
            "sandbox_name": "Box1",
            "account_name": "Account1",
            "farming_mode": "individual",
        },
        "game_settings": {
            "game_executable": "game.exe",
            "window_title_pattern": "Game",
            "expected_window_size": [1280, 720],
        },
        "coordinates": {
            "challenge_btn": [1, 2],
            "crusade_btn": [3, 4],
            "individual_btn": [5, 6],
            "fight_btn": [7, 8],
            "quick_btn": [9, 10],
            "ok_btn": [11, 12],
            "claim_btn": [13, 14],
            "enemy_coords": [[20, 30], [40, 50]],
        },
    }
    cfg = InstanceConfig.from_dict(data)
    assert cfg.enemy_coords == [Point(20, 30), Point(40, 50)]
