import logging
from dll.NKTP_DLL import *
from dll.register_enums import *
from scipy import constants

def set_bit(value, bit):
    return value | (1 << bit)

def clear_bit(value, bit):
    return value & ~(1 << bit)

class NKTBasik:
    def __init__(self, name = None, com = None):
        self.name = name
        self.com = com

        self.devID = None
    
    def query(self, register, index = None):
        if not index:
            index = -1
        result, value = RegTypeRead[register.name](
                                                    self.com, 
                                                    self.devID,
                                                    register.value,
                                                    index
        )
        if not isinstance(value, str):
            # rescale value
            value *= RegScaling[register.name].value
        return result, value

    def write(self, register, value, index = None):
        if not index:
            index = -1
        if not isinstance(value, str):
            # rescale value to match register
            value /= RegScaling[register.name].value
        RegTypeWrite[register.name](
                                    self.com,
                                    self.devID,
                                    register.value,
                                    value,
                                    index
        )

    def getSerialNumber(self):
        """Module serial number

        Returns:
            str: serial number
        """
        result, serial = self.query(RegLoc.SERIAL_NUMBER)
        return serial

    def getWavelengthCenter(self):
        """
        Wavelength center in nm
        """
        result, center = self.query(RegLoc.WAVELENGTH_CENTER)
        return center

    def getWavelengthOffset(self):
        """
        Wavelength offset setpoint in pm
        """
        result, offset = self.query(RegLoc.WAVELENGTH_OFFSET)
        return offset

    def getWavelengthOffsetReadout(self):
        """
        Wavelength offset readout in pm
        """
        result, offset = self.query(RegLoc.WAVLENGTH_OFFSET_READOUT)

    def getWavelength(self, units):
        """
        Wavelength in nm
        """
        center = self.getWavelengthCenter()
        offset = self.getWavelengthOffsetReadout()/1e3 # convert to nm
        return center + offset

    def setWavelength(self, wavelength):
        """Set wavelength offset

        Args:
            wavelength (int): wavelenght offset in nm
        """
        center = self.getWavelengthCenter()
        offset = int(wavelength - center)
        offset *= 1e3 # convert to pm
        self.write(RegLoc.WAVELENGTH_OFFSET, offset)

    def getWavelengthSetpoint(self):
        """
        Wavelength setpoint in nm
        """
        center = self.getWavelengthCenter()
        offset = self.getWavelengthOffset() * 1e3 # convert to nm
        return center + offset


    def getTemperature(self):
        """
        Module temperature in C
        """
        result, temperature = self.query(RegLoc.TEMPERATURE)
        return temperature

    def getEmission(self):
        """Module emission state

        Returns:
            bool: True = on, False = off
        """
        result, emission = self.query(RegLoc.EMISSION)
        return bool(emission)

    def setEmission(self, state):
        """Set module emission state

        Args:
            state (bool): True = on, False = off
        """
        self.write(RegLoc.EMISSION, int(state))

    def getPower(self):
        """Power output in mW

        Returns:
            float: power output in mW
        """
        result, power = self.query(RegLoc.OUTPUT_POWER)
        return power

    def getName(self):
        """Module name

        Returns:
            string: module name
        """
        result, name = self.query(RegLoc.NAME)
        return name

    def setName(self, name):
        """Set module name

        Args:
            name (str): module name
        """
        self.write(RegLoc.name, name)

    def getStatus(self):
        """Module status bits
        0 : emission
        1 : interlock off
        2 : -
        3 : -
        4 : module disabled
        5 : supply voltage low
        6 : module temperature range
        7 : -
        8 : -
        9 : -
        10: -
        11: waiting for temperature to drop
        12: -
        13: -
        14: wavelength stabilized (X15 only)
        15: error code present 

        Returns:
            int: status bits
        """
        result, status = self.query(RegLoc.STATUS)
        return status
    
    def getError(self):
        """Module error bits
        0: no error
        2: interlock
        3: low voltage
        7: module temperature range
        8: module disabled

        Returns:
            int: error bits
        """
        result, error = self.query(RegLoc.ERROR)
        return error
    
    def getModulationRange(self):
        """Module modulation range

        Returns:
            str: WIDE or NARROW
        """
        result, modulation_range = self.query(RegLoc.SETUP)
        modulation_range = modulation_range & 2**1
        return 'WIDE' if modulation_range else 'NARROW'

    def setModulationRange(self, modulation_range):
        """Set module modulation range

        Args:
            modulation_range (str): WIDE or NARROW modulation range
        """
        if modulation_range not in ['WIDE', 'NARROW']:
            logging.warning("NKTBasik setModulationRange(): invalid range" \
                            +"specified, valid entries are NARROW or WIDE")
            return

        result, setup = self.query(RegLoc.SETUP)
        modulation_range = 1 if modulation_range == 'WIDE' else 0

        range_bit = SetupBits.WIDE_WAVELENGTH_MODULATION
        setup = set_bit(setup, range_bit) if modulation_range \
                                                else clear_bit(setup, range_bit)

        self.write(RegLoc.SETUP, setup)

    #############################################
    # Some convenience functions
    #############################################

    def getFrequency(self):
        """Frequency in GHz

        Returns:
            float: frequency in GHz
        """
        center = self.getWavelengthCenter()
        offset = self.getWavelengthOffsetReadout() / 1e3
        return constants.c/(center + offset)

    def getFrequencySetpoint(self)
        """Frequency setpoint in GHz

        Returns:
            float: frequency setpoint in GHz
        """
        center = self.getWavelengthCenter()
        offset = self.getWavelengthOffset() / 1e3
        return constants.c/(center + offset)

    def setFrequency(self, frequency):
        """Set module frequency in GHz

        Args:
            frequency (float): frequency in GHz
        """
        self.setWavelength(constants.c/frequency)

    def moveFrequency(self, deviation):
        """Move module frequency in GHz

        Args:
            deviation (float): frequency deviation in GHz
        """
        frequency = self.getFrequency()
        self.setWavelength(constants.c/(frequency + deviation))