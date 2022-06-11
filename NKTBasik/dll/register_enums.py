from enum import Enum
from .NKTP_DLL import *
from functools import partial


class RegLoc(Enum):
    """
    Registry locations on NKT Photonics Basik K1x2 module
    """

    EMISSION = 0x30
    WAVELENGTH_OFFSET = 0x2A
    WAVELENGTH_CENTER = 0x32
    OUTPUT_POWER_mW = 0x17
    OUTPUT_POWER_dBm = 0x90
    OUTPUT_POWER_SETPOINT_mW = 0x22
    OUTPUT_POWER_SETPOINT_dBm = 0xA0
    TEMPERATURE = 0x1C
    SETUP = 0x31
    STATUS = 0x66
    ERROR = 0x67
    WAVELENGTH_OFFSET_READOUT = 0x72
    NAME = 0x8D

    SUPPLY_VOLTAGE = 0x1E
    SERIAL_NUMBER = 0x65

    WAVELENGTH_MODULATION = 0xB5

    MODULATION_SETUP = 0xB7

    WAVELENGTH_MODULATION_FREQUENCY = 0xB8  # 32-bit float, Hz
    WAVELENGTH_MODULATION_LEVEL = 0x2B  # 16-bit uint, permille
    WAVELENGTH_MODULATION_OFFSET = 0x2F  # 16-bit sint, permille
    AMPLITUDE_MODULATION_FREQUENCY = 0xBA
    AMPLITUDE_MODULATION_DEPTH = 0x2C


class RegTypeRead(Enum):
    """
    Registry types on NKT Photonics Basik K1x2 module
    """

    OUTPUT_POWER_mW = partial(registerReadU16)
    OUTPUT_POWER_dBm = partial(registerReadU16)
    OUTPUT_POWER_SETPOINT_mW = partial(registerReadS16)
    OUTPUT_POWER_SETPOINT_dBm = partial(registerReadS16)
    TEMPERATURE = partial(registerReadS16)
    SUPPLY_VOLTAGE = partial(registerReadU16)
    WAVELENGTH_OFFSET = partial(registerReadS16)
    WAVELENGTH_CENTER = partial(registerReadU32)
    WAVELENGTH_OFFSET_READOUT = partial(registerReadS16)
    EMISSION = partial(registerReadU8)
    NAME = partial(registerReadAscii)
    STATUS = partial(registerReadU8)
    ERROR = partial(registerReadU8)
    SETUP = partial(registerReadU16)
    SERIAL_NUMBER = partial(registerReadAscii)

    WAVELENGTH_MODULATION = partial(registerReadU8)

    MODULATION_SETUP = partial(registerReadU16)

    WAVELENGTH_MODULATION_FREQUENCY = partial(registerReadF32)
    WAVELENGTH_MODULATION_LEVEL = partial(registerReadU16)
    WAVELENGTH_MODULATION_OFFSET = partial(registerReadS16)
    AMPLITUDE_MODULATION_FREQUENCY = partial(registerReadF32)
    AMPLITUDE_MODULATION_DEPTH = partial(registerReadU16)

    # make register functions callable
    def __call__(self, *args):
        return self.value(*args)


def _write_ascii(*args):
    return registerWriteAscii(*args[:-1], 0, args[-1])


class RegTypeWrite(Enum):
    """
    Registry types on NKT Photonics Basik K1x2 module
    """

    WAVELENGTH_OFFSET = partial(registerWriteS16)
    WAVELENGTH_CENTER = partial(registerWriteU32)
    EMISSION = partial(registerWriteU8)
    NAME = partial(_write_ascii)
    SETUP = partial(registerWriteU16)
    OUTPUT_POWER_SETPOINT_dBm = partial(registerWriteS16)
    OUTPUT_POWER_SETPOINT_mW = partial(registerWriteS16)
    WAVELENGTH_MODULATION = partial(registerWriteU8)
    WAVELENGTH_MODULATION_FREQUENCY = partial(registerWriteF32)
    MODULATION_SETUP = partial(registerWriteU16)

    # make register functions callable
    def __call__(self, *args):
        return self.value(*args)


class RegScaling(Enum):
    """
    Registry readout scaling on NKT Photonics Basik K1x2 module
    """

    OUTPUT_POWER = 0.01
    TEMPERATURE = 0.1
    SUPPLY_VOLTAGE = 0.001
    WAVELENGTH_OFFSET = 0.1
    WAVELENGTH_CENTER = 0.0001
    WAVELENGTH_OFFSET_READOUT = 0.1
    OUTPUT_POWER_SETPOINT_mW = 0.01
    OUTPUT_POWER_SETPOINT_dBm = 0.01
    WAVELENGTH_MODULATION_LEVEL = 0.1
    WAVELENGTH_MODULATION_OFFSET = 0.1


class RegUnits(Enum):
    OUTPUT_POWER_mW = "mW"
    OUTPUT_POWER_dBm = "dBm"
    OUTPUT_POWER_SETPOINT_mW = "mW"
    OUTPUT_POWER_SETPOINT_dBm = "dBm"

    TEMPERATURE = "C"
    SUPPLY_VOLTAGE = "V"

    WAVELENGTH_OFFSET = "pm"
    WAVELENGTH_CENTER = "nm"
    WAVELENGTH_OFFSET_READOUT = "pm"
    EMISSION = "bool"

    WAVELENGTH_MODULATION_FREQUENCY = "Hz"
    WAVELENGTH_MODULATION_LEVEL = "permille"
    WAVELENGTH_MODULATION_OFFSET = "permille"
    AMPLITUDE_MODULATION_FREQUENCY = "Hz"

