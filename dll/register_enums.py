from enum import Enum
from functools import partial

class RegLoc(Enum):
    """
    Registry locations on NKT Photonics Basik K1x2 module
    """
    EMISSION            = 0x30
    WAVELENGTH_OFFSET   = 0x2A
    WAVELENGTH_CENTER   = 0x32
    OUTPUT_POWER        = 0x17
    TEMPERATURE         = 0x1C
    SETUP               = 0x31
    STATUS              = 0x66
    ERROR               = 0x67
    CURRENT_OFFSET      = 0x72
    NAME                = 0x8D
    
    SUPPLY_VOLTAGE      = 0x1E
    SERIAL_NUMBER       = 0x65

class RegTypeRead(Enum):
    """
    Registry types on NKT Photonics Basik K1x2 module
    """
    OUTPUT_POWER                = partial(registerReadU16)
    TEMPERATURE                 = partial(registerReadS16)
    SUPPLY_VOLTAGE              = partial(registerReadU16)
    WAVELENGTH_OFFSET           = partial(registerReadS16)
    WAVELENGTH_CENTER           = partial(registerReadU32)
    WAVELENGTH_OFFSET_READOUT   = partial(registerReadS16)
    EMISSION                    = partial(registerReadU8)
    NAME                        = partial(registerReadAscii)
    STATUS                      = partial(registerReadU8)
    ERROR                       = partial(registerReadU8)
    SETUP                       = partial(registerReadU16)
    SERIAL_NUMBER               = partial(registerReadAscii)

    # make register functions callable
    def __call__(self, *args):
        return self.value(*args)

class RegTypeWrite(Enum):
    """
    Registry types on NKT Photonics Basik K1x2 module
    """
    WAVELENGTH_OFFSET           = partial(registerWriteS16)
    WAVELENGTH_CENTER           = partial(registerWriteU32)
    EMISSION                    = partial(registerWriteU8)
    NAME                        = partial(registerWriteAscii)
    SETUP                       = partial(registerWriteU16)

    # make register functions callable
    def __call__(self, *args):
        return self.value(*args)

class RegScaling(Enum):
    """
    Registry readout scaling on NKT Photonics Basik K1x2 module
    """
    OUTPUT_POWER                = 0.01
    TEMPERATURE                 = 0.1
    SUPPLY_VOLTAGE              = 0.001
    WAVELENGTH_OFFSET           = 0.1
    WAVELENGTH_CENTER           = 0.0001
    WAVELENGTH_OFFSET_READOUT   = 0.1
    EMISSION                    = 1
    STATUS                      = 1
    ERROR                       = 1
    SETUP                       = 1

class RegUnits(Enum):
    OUTPUT_POWER                = 'mW'
    TEMPERATURE                 = 'C'
    SUPPLY_VOLTAGE              = 'V'

    WAVELENGTH_OFFSET           = 'pm'
    WAVELENGTH_CENTER           = 'nm'
    WAVELENGTH_OFFSET_READOUT   = 'pm'
    EMISSION                    = 'bool'

class StatusBits(Enum):
    EMISSION                = 0
    INTERLOCK_OFF           = 1
    DISABLED                = 4
    SUPPLY_VOLTAGE_LOW      = 5
    MODULE_TEMP_RANGE       = 6 
    WAITING_TEMPERATURE     = 11
    WAVELENGTH_STABILIZED   = 14
    ERROR_CODE_PRESENT      = 15

class ErrorBits(Enum):
    NO_ERROR                    = 0
    INTERLOCK                   = 2
    LOW_VOLTAGE                 = 3
    MODULE_TEMPERATURE_RANGE    = 7
    MODULE_DISABLED             = 8

class SetupBits(Enum):
    WIDE_WAVELENGTH_MODULATION              = 1
    EXTERNAL_WAVELENGTH_MODULATION          = 2
    WAVELENGTH_MODULATION_DC                = 3
    INTERNAL_WAVELENGTH_MODULATION          = 4
    MODULATION_OUTPUT                       = 5
    PUMP_OPERATION_CONSTANT_CURRENT         = 8
    EXTERNAL_AMPLITUDE_MODULATION_SOURCE    = 9