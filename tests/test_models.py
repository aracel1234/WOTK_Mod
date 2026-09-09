from __future__ import annotations

import pytest

from wotk.models import MarchState, QuestDelays, WarSettings


def test_quest_delays_validate_with_slots():
    QuestDelays(default=0.1, navigation=0.2, combat=0.3, reward=0.4).validate()


def test_march_state_next_city_has_no_off_by_one():
    state = MarchState(current_index=0)
    route = ["Kota1", "Kota2", "Kota3"]
    assert state.next_city(route) == "Kota2"
    state.mark_success("Kota2", route)
    assert state.current_index == 1
    assert state.next_city(route) == "Kota3"


def test_war_settings_reject_same_account_and_target_color():
    settings = WarSettings(
        account_count=2,
        target_color="merah",
        account_colors=["hijau", "merah"],
        city_route=["Dongxing"],
    )
    with pytest.raises(ValueError):
        settings.validate()


def test_war_settings_prepends_target_city():
    settings = WarSettings(
        account_count=1,
        target_color="biru",
        account_colors=["merah"],
        city_route=["Mianzhu"],
    )
    settings.validate()
    assert settings.city_route[0] == "WeiXian"
