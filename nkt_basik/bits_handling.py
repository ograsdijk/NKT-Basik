from dataclasses import dataclass
from enum import IntEnum


@dataclass
class BasikState:
    def to_list_set(self):
        return [
            name
            for name, field in self.__dataclass_fields__.items()
            if getattr(self, field.name)
        ]


class StatusBits(IntEnum):
    EMISSION = 0
    INTERLOCK_OFF = 1
    DISABLED = 4
    SUPPLY_VOLTAGE_LOW = 5
    MODULE_TEMP_RANGE = 6
    WAITING_TEMPERATURE = 11
    WAVELENGTH_STABILIZED = 14
    ERROR_CODE_PRESENT = 15


class ErrorBits(IntEnum):
    NO_ERROR = 0
    INTERLOCK = 2
    LOW_VOLTAGE = 3
    MODULE_TEMPERATURE_RANGE = 7
    MODULE_DISABLED = 8


class SetupBits(IntEnum):
    NARROW_WAVELENGTH_MODULATION = 1
    EXTERNAL_WAVELENGTH_MODULATION = 2
    WAVELENGTH_MODULATION_DC = 3
    INTERNAL_WAVELENGTH_MODULATION = 4
    MODULATION_OUTPUT = (
        5  # output the wavelength modulation signal on the wavelength pins
    )
    PUMP_OPERATION_CONSTANT_CURRENT = 8
    EXTERNAL_AMPLITUDE_MODULATION_SOURCE = 9


class ModulationSetupBits(IntEnum):
    AMPLITUDE_MODULATION_FREQUENCY_SELECTOR = 0
    AMPLITUDE_MODULATION_WAVEFORM = 2  # 0 = sine, 1 = triangle
    WAVELENGTH_MODULATION_FREQUENCY_SELECTOR = 4


class Bits:
    def __init__(self, value: int):
        self.value = value

    def get_set_bits(self) -> list[int]:
        return [i for i in range(self.value.bit_length()) if (self.value >> i & 1)]

    def set_bit(self, bit: int, bit_value: int) -> None:
        bit_value = 1 if bit_value else 0
        value = self.value if self.value else 0
        value = value | (1 << bit) if bit_value else value & ~(1 << bit)
        self.value = value

    def get_bit(self, bit: int) -> int:
        return self.value >> bit & 1

    def set_value(self, enum: int, val: int) -> None:
        self.set_bit(enum, val)

    def get_value(self, enum: int) -> int:
        return self.get_bit(enum)


@dataclass
class BasikStatus(BasikState):
    EMISSION: bool
    INTERLOCK_OFF: bool
    DISABLED: bool
    SUPPLY_VOLTAGE_LOW: bool
    MODULE_TEMP_RANGE: bool
    WAITING_TEMPERATURE: bool
    WAVELENGTH_STABILIZED: bool
    ERROR_CODE_PRESENT: bool


class NKTStatus(Bits):
    def __init__(self, value: int):
        super().__init__(value)

    def get_status(self) -> BasikStatus:
        return BasikStatus(
            **dict((en.name, bool(self.get_bit(en.value))) for en in StatusBits)
        )


@dataclass
class BasikError(BasikState):
    NO_ERROR: bool
    INTERLOCK: bool
    LOW_VOLTAGE: bool
    MODULE_TEMPERATURE_RANGE: bool
    MODULE_DISABLED: bool


class NKTError(Bits):
    def __init__(self, value: int):
        super().__init__(value)

    def get_errors(self) -> BasikError:
        return BasikError(
            **dict((en.name, bool(self.get_bit(en.value))) for en in ErrorBits)
        )


@dataclass
class BasikSetup(BasikState):
    NARROW_WAVELENGTH_MODULATION: bool
    EXTERNAL_WAVELENGTH_MODULATION: bool
    WAVELENGTH_MODULATION_DC: bool
    INTERNAL_WAVELENGTH_MODULATION: bool
    MODULATION_OUTPUT: bool
    PUMP_OPERATION_CONSTANT_CURRENT: bool
    EXTERNAL_AMPLITUDE_MODULATION_SOURCE: bool


class NKTSetup(Bits):
    def __init__(self, value: int):
        super().__init__(value)

    def get_setup(self) -> BasikSetup:
        return BasikSetup(
            **dict((en.name, bool(self.get_bit(en.value))) for en in SetupBits)
        )


class ModulationWaveform(IntEnum):
    SINE = 0
    TRIANGLE = 1
    SAWTOOTH = 2
    INVERSE_SAWTOOTH = 3


class NKTModulationSetup(Bits):
    def __init__(self, value=None):
        super().__init__(0 if value is None else value)

    def get_setup(self) -> dict[str, int | str]:
        setup: dict[str, int | str] = {}
        for bit in [0, 2, 4]:
            setup[ModulationSetupBits(bit).name] = self.get_bit(
                ModulationSetupBits(bit).value
            )

        # last 2 bits specify modulation waveform
        setup["MODULATION_WAVEFORM"] = ModulationWaveform(self.value >> 6).name
        return setup

    def get_waveform(self) -> ModulationWaveform:
        return ModulationWaveform(self.value >> 6)

    def set_waveform(self, waveform: ModulationWaveform) -> None:
        # value = self.value if self.value else 0
        # value = value | (1 << bit) if bit_value else value & ~(1 << bit)
        # self.value = value
        wf = waveform.value << 6

        value = self.value if self.value else 0
        if waveform.value:
            value = value | wf
            self.value = value
        else:
            self.set_bit(6, 0)
            self.set_bit(7, 0)
