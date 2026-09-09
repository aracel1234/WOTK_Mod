# Requirement traceability

This matrix maps the supporting design to the final repository implementation.

| Requirement from supporting material | Implementation |
|---|---|
| Static coordinate calibration | GUI `CoordinateEditor`; JSON profile templates |
| OCR area calibration for Watch / city-selection text | GUI `RegionEditor`; `OcrService`; `WarEngine` |
| Account count and target color | `WarSettings` validation |
| Per-account alliance color cannot equal attack target | `WarSettings.validate()` |
| Color target mapping Mianzhu / Dongxing / WeiXian | `COLOR_TO_CITY` |
| Search → Fight → Dispatch → Minimize | `WarEngine.fight_round()` |
| Watch detection | required `watch_area` + `WarEngine._has_watch()` |
| Optional general-count March condition (player − enemy >= threshold) | `use_general_threshold`, OCR count regions, `march_threshold` |
| March and `Please Select the city you want to visit` | `WarEngine.march_chain()` |
| `No hero can march` → Back | optional `no_hero_area` + March fallback |
| Chained Assault where successful city becomes current city | `MarchState` + iterative `march_chain()` |
| Assault retries | `WarSettings.assault_retries` + `_perform_assault()` |
| 31-minute cycle | `WarSettings.cycle_minutes` default 31.0 |
| `Ctrl+Tab` account rotation | `AutomationContext.switch_tab()` |
| Individual quest 1–10 stages | `IndividualEngine` |
| Mysteriland 1–5 stages and 1x/5x swipe | `MysterilandEngine` |
| Supremacy 12 challenge choices | `SupremacyEngine.CHALLENGE_NAMES` flow |
| Supremacy phase 1 / phase 2 | `initial_phase_loops` + hero selection |
| Multi-instance master/instance JSON | `MultiInstanceMaster`, `InstanceConfig` |
| Sandboxie launch | `SandboxieManager` (existing boxes only) |
| Client-relative coordinate conversion | `WindowManager.client_rect()` + `RelativeInstanceRunner.click_rel()` |
| Per-instance thread management | `ThreadPoolExecutor` |
| Focus window before input | `RelativeInstanceRunner.click_rel()` |
| Logging | rotating file logger + GUI event log |
| Emergency stop hotkey | best-effort `EmergencyHotkey` + GUI Stop + PyAutoGUI FAILSAFE |
| Error isolation/recovery | validation, window reacquire, Stop propagation, bounded retries |

## Deliberate design clarifications

The document describes independent instance threads. The final implementation preserves thread-level
instance management but serializes actual physical input. This is required because PyAutoGUI is not
an independent per-window input channel.

The document also describes creating/configuring Sandboxie templates and resource/isolation policy.
The repository does not automatically modify those security settings; it only launches into an
**existing** named sandbox. Sandbox creation and policy remain explicit user administration steps.
