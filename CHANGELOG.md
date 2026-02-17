# Changelog

All notable changes to this project are documented in this file.

## 0.4.1 - 2026-02-16

### Added
- Added `Basik.supply_voltage` property to expose the `SUPPLY_VOLTAGE` register.
- Added tests for `supply_voltage` and enum/int setter validation.

### Changed
- Setters for `mode`, `modulation_source`, `modulation_range`, `modulation_coupling`, and `modulation_waveform` now accept either enum members or integer values.
- Integer setter values are validated against allowed enum values and return clearer `BasikTypeError` messages.
- Modernized type hints for Python 3.11+ (`|`, `list[...]`, `dict[...]`).
- Updated register scaling enum keys to `OUTPUT_POWER_mW` and `OUTPUT_POWER_dBm`.
- Bumped package version to `0.4.1`.
