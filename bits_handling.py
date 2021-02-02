import logging
from enum import Enum
from dll.register_enums import StatusBits, ErrorBits, SetupBits, ModulationSetupBits

class Bits:
    def __init__(self, value, enum):
        self.value = value
        self.enum = enum
    
    def getSetBits(self):
        return [i for i in range(self.value.bit_length()) if (self.value >> i & 1)]

    def setBit(self, bit, bit_value):
        value = self.value if self.value else 0
        value = value | (1 << bit) if bit_value else value & ~(1 << bit)
        self.value = value
    
    def getBit(self, bit):
        return self.value >> bit & 1

    def setValue(self, enum, val):
        self.setBit(enum.value, val)

    def getValue(self, enum):
        return self.getBit(enum.value)

    
class NKTStatus(Bits):
    def __init__(self, value, enum = StatusBits):
        super().__init__(value, enum)

    def getStatus(self):
        status = []
        for bit in self.getSetBits():
            try:
                status.append(self.enum(bit).name)
            except ValueError:
                logging.warning(f'Status bit {bit} not defined')
        return status

    
class NKTError(Bits):
    def __init__(self, value, enum = ErrorBits):
        super().__init__(value, enum)

    def getErrors(self):
        errors = []
        for bit in self.getSetBits():
            try:
                errors.append(self.enum(bit).name)
            except ValueError:
                logging.warning(f'Error bit {bit} not defined')
        return errors


class NKTSetup(Bits):
    def __init__(self, value, enum = SetupBits):
        super().__init__(value, enum)

    def getSetup(self):
        return dict([(en.name, bool(self.getBit(en.value))) for en in self.enum])


class ModulationWaveform(Enum):
    SINE                = 0
    TRIANGLE            = 1
    SAWTOOTH            = 2
    INVERSE_SAWTOOTH    = 3

class NKTModulationSetup(Bits):
    def __init__(self, value = None, enum = ModulationSetupBits):
        super().__init__(value, enum)

    def getSetup(self):
        setup = {}
        for bit in [0,2,4]:
            setup[self.enum(bit).name] = self.getBit(self.enum(bit).value)

        # last 2 bits specify modulation waveform
        setup['MODULATION_WAVEFORM'] = ModulationWaveform(self.value >> 6).name
        return setup

        