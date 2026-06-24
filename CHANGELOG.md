# Changelog

All notable changes to this project are documented in this file.

## 0.5.0 - 2026-06-23

### Added
- `read_paramset()` and `describe()` expose the device-reported parameter set
  (unit, setpoint, factory default, min/max limits) for settings registers.
- Opt-in `validate_writes` constructor flag: scalar setters validate the value
  against the parameter-set limits and raise `ValueError` instead of issuing a
  write the module would reject.
- `amplitude_modulation_depth` property for the intensity amplitude-modulation
  depth register (`0x2C`).
- Exported `ParamSet` and added the `EXTERNAL_MODULATION_GAIN` register.

### Fixed
- `modulation_gain` now targets the external (piezo) wavelength-modulation gain
  — the high word of register `0xA1` at index 2 (NKT CONTROL's 0–250 % slider) —
  instead of `AMPLITUDE_MODULATION_DEPTH` (`0x2C`, the intensity AM depth).
  Previously the value read back correctly but the modulation gain never changed.

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
