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


def test_mode_setter_accepts_int_value() -> None:
    device = make_device()
    writes: list[tuple[RegLoc, int, int]] = []

    device.query = lambda *_args, **_kwargs: 0  # type: ignore[method-assign]
    device.write = lambda reg, value, index=-1: writes.append((reg, value, index))  # type: ignore[method-assign]

    device.mode = 1
    assert writes


def test_mode_setter_rejects_out_of_range_int() -> None:
    device = make_device()
    device.query = lambda *_args, **_kwargs: 0  # type: ignore[method-assign]

    try:
        device.mode = 2
    except BasikTypeError as exc:
        assert "(0, 1)" in str(exc)
    else:
        raise AssertionError("Expected BasikTypeError for out-of-range mode int")


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

    for invalid in ("narrow", None, 3, True):
        try:
            device.modulation_range = invalid  # type: ignore[assignment]
        except BasikTypeError:
            continue
        raise AssertionError("Expected BasikTypeError for invalid modulation_range")


def test_modulation_enum_setters_accept_int_values() -> None:
    device = make_device()
    writes: list[tuple[RegLoc, int, int]] = []

    device.query = lambda reg, index=-1: 0  # type: ignore[method-assign]
    device.write = lambda reg, value, index=-1: writes.append((reg, value, index))  # type: ignore[method-assign]

    device.modulation_source = 3
    device.modulation_range = 1
    device.modulation_coupling = 1
    device.modulation_waveform = 2

    assert len(writes) == 4


def test_modulation_enum_setters_reject_out_of_range_ints() -> None:
    device = make_device()
    device.query = lambda reg, index=-1: 0  # type: ignore[method-assign]

    invalid_cases = [
        ("modulation_source", 0),
        ("modulation_range", 2),
        ("modulation_coupling", 2),
        ("modulation_waveform", 4),
    ]

    for attr, invalid in invalid_cases:
        try:
            setattr(device, attr, invalid)
        except BasikTypeError:
            continue
        raise AssertionError(f"Expected BasikTypeError for invalid {attr} int")


def test_supply_voltage_property_reads_register() -> None:
    device = make_device()

    def fake_query(reg: RegLoc, index: int = -1):
        assert reg == RegLoc.SUPPLY_VOLTAGE
        assert index == -1
        return 24.5

    device.query = fake_query  # type: ignore[method-assign]

    assert device.supply_voltage == 24.5
