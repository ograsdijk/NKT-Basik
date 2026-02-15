from nkt_basik import (
    Basik,
    LaserMode,
    ModulationCoupling,
    ModulationRange,
    ModulationSource,
)
from nkt_basik.bits_handling import ModulationWaveform, NKTSetup, SetupBits
from nkt_basik.dll.register_enums import RegLoc
from nkt_basik.module import BasikTypeError


def make_device() -> Basik:
    device = Basik.__new__(Basik)
    device.port = "COM_TEST"
    device.devID = 1
    return device


def test_mode_setter_requires_enum() -> None:
    device = make_device()
    writes: list[tuple[RegLoc, int, int]] = []

    device.query = lambda *_args, **_kwargs: 0  # type: ignore[method-assign]
    device.write = lambda reg, value, index=-1: writes.append((reg, value, index))  # type: ignore[method-assign]

    device.mode = LaserMode.CURRENT
    assert writes

    try:
        device.mode = "current"  # type: ignore[assignment]
    except BasikTypeError:
        pass
    else:
        raise AssertionError("Expected BasikTypeError for non-enum mode")


def test_modulation_source_bit_mapping() -> None:
    device = make_device()
    writes: list[tuple[RegLoc, int, int]] = []

    device.query = lambda *_args, **_kwargs: 0  # type: ignore[method-assign]
    device.write = lambda reg, value, index=-1: writes.append((reg, value, index))  # type: ignore[method-assign]

    device.modulation_source = ModulationSource.INTERNAL
    _, setup_raw, _ = writes[-1]
    setup = NKTSetup(setup_raw)

    assert setup.get_value(SetupBits.INTERNAL_WAVELENGTH_MODULATION) == 1
    assert setup.get_value(SetupBits.EXTERNAL_WAVELENGTH_MODULATION) == 0


def test_modulation_enum_setters_require_enum_values() -> None:
    device = make_device()
    writes: list[tuple[RegLoc, int, int]] = []

    device.query = lambda reg, index=-1: 0  # type: ignore[method-assign]
    device.write = lambda reg, value, index=-1: writes.append((reg, value, index))  # type: ignore[method-assign]

    device.modulation_range = ModulationRange.NARROW
    device.modulation_coupling = ModulationCoupling.DC
    device.modulation_waveform = ModulationWaveform.SAWTOOTH

    assert len(writes) == 3

    for invalid in ("narrow", 1, None):
        try:
            device.modulation_range = invalid  # type: ignore[assignment]
        except BasikTypeError:
            continue
        raise AssertionError("Expected BasikTypeError for invalid modulation_range")
