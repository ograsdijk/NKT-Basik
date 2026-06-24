from nkt_basik import (
    Basik,
    LaserMode,
    ModulationCoupling,
    ModulationRange,
    ModulationSource,
)
import nkt_basik.module as module
from nkt_basik.bits_handling import ModulationWaveform, NKTSetup, SetupBits
from nkt_basik.dll.register_enums import RegLoc
from nkt_basik.module import BasikConnectionError, BasikTypeError


def make_device() -> Basik:
    device = Basik.__new__(Basik)
    device.port = "COM_TEST"
    device.devID = 1
    return device


def test_connect_closes_port_when_device_create_fails(monkeypatch) -> None:
    closed_ports: list[str] = []

    monkeypatch.setattr(module, "openPorts", lambda *_args, **_kwargs: 0)
    monkeypatch.setattr(module, "deviceCreate", lambda *_args, **_kwargs: 3)
    monkeypatch.setattr(module, "closePorts", closed_ports.append)

    try:
        Basik("COM_TEST", 1)
    except BasikConnectionError:
        pass
    else:
        raise AssertionError("Expected BasikConnectionError")

    assert closed_ports == ["COM_TEST"]


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


def test_modulation_level_offset_and_depth_setters_write_registers() -> None:
    device = make_device()
    writes: list[tuple[RegLoc, float, int]] = []

    device.write = lambda reg, value, index=-1: writes.append((reg, value, index))  # type: ignore[method-assign]

    device.modulation_level = 12.3
    device.modulation_offset = -4.5
    device.modulation_gain = 6.7
    device.amplitude_modulation_depth = 8.9

    assert writes == [
        (RegLoc.WAVELENGTH_MODULATION_LEVEL, 12.3, -1),
        (RegLoc.WAVELENGTH_MODULATION_OFFSET, -4.5, -1),
        # external piezo modulation gain lives in the high word of 0xA1 (index 2)
        (RegLoc.EXTERNAL_MODULATION_GAIN, 6.7, 2),
        (RegLoc.AMPLITUDE_MODULATION_DEPTH, 8.9, -1),
    ]


def test_supply_voltage_property_reads_register() -> None:
    device = make_device()

    def fake_query(reg: RegLoc, index: int = -1):
        assert reg == RegLoc.SUPPLY_VOLTAGE
        assert index == -1
        return 24.5

    device.query = fake_query  # type: ignore[method-assign]

    assert device.supply_voltage == 24.5


def _paramset_bytes(unit, startval, factory, ulimit, llimit, *, signed=False):
    """Build a 16-byte tParamSetStruct block (Num=Den=1, Offset=0)."""

    def w(v):
        return int(v).to_bytes(2, "little", signed=signed)

    return (
        bytes([unit, 0])
        + w(startval)
        + w(factory)
        + w(ulimit)
        + w(llimit)
        + b"\x01\x00\x01\x00\x00\x00"
    )


def test_read_paramset_parses_gain(monkeypatch) -> None:
    device = make_device()
    # the gain paramset lives at 0xD3 (override): PerMille, SV 2003, range [37, 2569]
    blocks = {0xD3: _paramset_bytes(18, 2003, 0, 2569, 37)}
    monkeypatch.setattr(
        module,
        "registerRead",
        lambda port, dev, reg, index: (0, blocks[reg]) if reg in blocks else (4, b""),
    )

    ps = device.read_paramset(RegLoc.EXTERNAL_MODULATION_GAIN)
    assert ps is not None
    assert ps.unit == "PerMille"
    assert round(ps.value, 1) == 200.3
    assert round(ps.min, 1) == 3.7
    assert round(ps.max, 1) == 256.9
    assert device.describe(RegLoc.EXTERNAL_MODULATION_GAIN)["max"] == ps.max


def test_read_paramset_handles_signed_offset(monkeypatch) -> None:
    device = make_device()
    # wavelength modulation offset (0x2F -> 0x5F) is signed; limits +/-1000 permille
    blocks = {0x5F: _paramset_bytes(18, 0, 0, 1000, -1000, signed=True)}
    monkeypatch.setattr(
        module,
        "registerRead",
        lambda port, dev, reg, index: (0, blocks[reg]) if reg in blocks else (4, b""),
    )

    ps = device.read_paramset(RegLoc.WAVELENGTH_MODULATION_OFFSET)
    assert ps is not None
    assert round(ps.min, 1) == -100.0
    assert round(ps.max, 1) == 100.0


def test_read_paramset_none_for_non_paramset(monkeypatch) -> None:
    device = make_device()
    # emission (0x30 -> 0x60) is a 1-byte register, not a paramset
    monkeypatch.setattr(module, "registerRead", lambda *a, **k: (0, b"\x00"))
    assert device.read_paramset(RegLoc.EMISSION) is None
    assert device.describe(RegLoc.EMISSION) is None


def test_read_paramset_rejects_garbage(monkeypatch) -> None:
    device = make_device()
    # 16 bytes but bogus unit code -> not a real paramset -> None
    junk = bytes([117, 0]) + (1000).to_bytes(2, "little") * 6 + b"\x00\x00\x00\x00"
    monkeypatch.setattr(module, "registerRead", lambda *a, **k: (0, junk))
    assert device.read_paramset(RegLoc.WAVELENGTH_MODULATION_LEVEL) is None


def test_validate_writes_enforces_limits(monkeypatch) -> None:
    device = make_device()
    device._validate_writes = True
    writes: list[tuple[RegLoc, float, int]] = []
    device.write = lambda reg, value, index=-1: writes.append((reg, value, index))  # type: ignore[method-assign]
    blocks = {0xD3: _paramset_bytes(18, 2000, 0, 2569, 37)}
    monkeypatch.setattr(
        module,
        "registerRead",
        lambda port, dev, reg, index: (0, blocks[reg]) if reg in blocks else (4, b""),
    )

    device.modulation_gain = 150.0  # within [3.7, 256.9] -> writes
    assert writes == [(RegLoc.EXTERNAL_MODULATION_GAIN, 150.0, 2)]

    try:
        device.modulation_gain = 300.0  # above max -> rejected before writing
    except ValueError as exc:
        assert "256.9" in str(exc)
    else:
        raise AssertionError("expected ValueError for out-of-range gain")
    assert len(writes) == 1  # the rejected write never happened
