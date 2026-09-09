from __future__ import annotations

from wotk.config_store import ConfigStore


def test_config_store_atomic_round_trip(tmp_path):
    store = ConfigStore(tmp_path / "config")
    store.save_json("war/test.json", {"value": 42})
    assert store.load_json("war/test.json") == {"value": 42}
