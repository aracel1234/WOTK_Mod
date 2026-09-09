# Configuration reference

## Auto Login

Required coordinate names:

`login_username`, `login_password`, `login_button`, `signup_button`, `reg_username`,
`reg_password`, `reg_confirm`, `reg_button`, `play_now`, `address_bar`, `id_button`, `logout_button`.

Each account has `username`, `password`, `confirm_password`, `action_type` (`login`/`register`), and
`server_number`. Account data is not persisted by the normal GUI Profile Save function.

## Individual

Required static points are `challenge_button`, `crusade_button`, `individual_button`,
`fight_button`, `quick_combat`, `ok_button`, and `claim_button` plus `stage_N` and `reward_N` for
every selected stage. Up to 10 stages are supported.

## Mysteriland

Static points:

`challenge`, `crusade`, `mysteriland`, `enter_challenge`, `fight`, `quick_combat`, `ok`,
`swipe_1x`, `swipe_5x`, `exit`.

Stage coordinates use `stage_1..5` and `reward_1..5` and can be stored separately for `senin` through `sabtu` under `stage_coordinates_by_day`.

## Supremacy

Settings:

- `max_loops`: 1–50;
- `initial_phase_loops`: direct-fight loops before hero selection;
- `total_heroes`: 1–8;
- `heroes_per_battle`: number selected in phase 2;
- `max_hero_usage`: per-rotation usage cap;
- `selected_challenge`: 1–12.

Coordinates include six visible challenge slots and Hero 1–8.

## Auto War

### Settings

- `account_count`: 1–10;
- `target_color`: `hijau`, `merah`, or `biru`;
- `account_colors`: one alliance color per account, not equal to target;
- `city_route`: ordered March/Assault targets;
- `cycle_minutes`: defaults to 31;
- `march_enabled`;
- `max_march_hops`;
- `assault_retries`;
- `post_cycle_pause`;
- `use_general_threshold` and `march_threshold` for the earlier general-count March condition.

### Runtime

- `default_delay`;
- `combat_delay`;
- `tab_delay`;
- `march_check_interval_seconds`;
- `tesseract_cmd` (optional);
- `max_cycles`: integer or `null` for continuous mode;
- `initialize_maps`.

### Required coordinates

`bendera_biru`, `search`, `field_search`, `konfirmasi_search`, `nama_kota`, `fight`, `dispatch`,
`minimize`, `watch`, `march`, `back`, `exit`.

### Optional Assault coordinates

`assault_search`, `assault_field_search`, `assault_confirm_search`, `assault_city`,
`assault_button`, `march_confirm`.

If optional search points are not configured, the normal Search points are reused.

### OCR regions

Required: `watch_area`, `select_city_area`.

Optional: `defender_area`, `no_hero_area`, `assault_area`, `player_general_area`, and `enemy_general_area`. The two general areas are required only when `use_general_threshold` is enabled.

## Multi-instance

Master config controls Sandboxie path, maximum instances, startup delay, global timing, retry count,
emergency hotkey, and thread pool size.

Each instance config has:

- `instance_info`: id, sandbox name, account label, mode;
- `game_settings`: game executable, window title pattern, window index, expected client size,
  optional offset correction;
- `coordinates`: mode-specific client-relative points and point arrays;
- `timing_settings`;
- `max_cycles` and `cycle_delay`.

See the JSON under `config/examples/` for exact shapes.
