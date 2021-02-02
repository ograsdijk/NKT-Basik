import logging
from enum import Enum
from .dll.register_enums import RegLoc, RegTypeRead, RegScaling, RegTypeWrite
from .bits_handling import NKTStatus, NKTError, NKTSetup, NKTModulationSetup, \
                            SetupBits
from .dll.NKTP_DLL import openPorts, closePorts, deviceCreate, \
                            RegisterResultTypes, DeviceResultTypes

class constants(Enum):
    c   = 299792458.0

class Basik:
    """Interface for an NKT Basik fiber seed laser from NKT Photonics

    Args:
        port (str): COM port of the seed laser
        devID (int): device ID of the seed laser

    Attributes:
        port (str)  : COM port of the seed laser
        devID (int) : device ID of the seed laser
    
    Methods:
        query(register, index)
        write(register, value, index)
        getSerialNumber()
        setCurrentMode()
        setPowerMode()
        getOutputPowerSetpoint()
        setOutputPowerSetpoint(power)
        getWavelengthCenter()
        getWavelengthOffset()
        setWavelengthOffset(offset)
        getWavelengthOffsetReadout()
        getWavelength()
        setWavelength()
        getWavelengthSetpoint()
        getTemperature()
        getEmission()
        setEmission()
        getName()
        setName(name)
        getStatusBits()
        getStatus()
        getErrorBits()
        getError()
        setModulation(enable)
        getModulation()
        getModulationRange()
        setModulationRange(modulation_range)
        getFrequency()
        getFrequencySetpoint()
        setFrequency(frequency)
        moveFrequency(deviation)

    """
    def __init__(self, port, devID):
        """Initialize NKT Basik module

        Args:
            port (str): COM port of the seed laser
            devID (int): device ID of the seed laser
        """
        self.port = port
        self.devID = devID

        device_result = openPorts(port, 0, 0)
        if device_result != 0:
            device_result = DeviceResultTypes(device_result).split(':')[-1]
            logging.error(f'Basik opening port {port}: {device_result}')

        device_result = deviceCreate(port, devID, 1)
        if device_result != 0:
            device_result = DeviceResultTypes(device_result).split(':')[-1]
            logging.error(f'Basik creating device {devID} on port {port}: {device_result}')

    def query(self, register, index = -1):
        """Query a register on a NKT Basik module

        Args:
            register (enum): RegLoc enum containing register locations
            index (int, optional): register index. Defaults to -1.

        Returns:
            (int, float, str): value of the register. Type depends on the 
                                specified register.
        """
        register_result, value = RegTypeRead[register.name](
                                                    self.port, 
                                                    self.devID,
                                                    register.value,
                                                    index
        )
        if register_result != 0:
            register_result = RegisterResultTypes(register_result).split(':')[-1]
            logging.error(f'Basik query({register.name}, {index}): {register_result}')
            return None

        if isinstance(value, bytes):
            value = value.decode()

        try:
            # rescale value
            value *= RegScaling[register.name].value
        except KeyError:
            pass
        return value

    def write(self, register, value, index = -1):
        """Write to a register on an NKT Basik module

        Args:
            register (enum): enum containing register locations
            value (int, float, str): value to write to register
            index (int, optional): register index. Defaults to -1.
        """
        try:
            value /= RegScaling[register.name].value
            value = int(value)
        except KeyError:
            pass
        register_result = RegTypeWrite[register.name](
                                                        self.port,
                                                        self.devID,
                                                        register.value,
                                                        value,
                                                        index
                                                        )
        if register_result != 0:
            register_result = RegisterResultTypes(register_result).split(':')[-1]
            logging.error(f"Basik write({register.name}, {value}, {index}: {register_result}")

    def getSerialNumber(self):
        """Module serial number

        Returns:
            str: serial number
        """
        serial = self.query(RegLoc.SERIAL_NUMBER)
        return serial

    def setCurrentMode(self):
        """Set device in constant current mode
        """
        setup = NKTSetup(self.query(RegLoc.SETUP))
        setup.setValue(SetupBits.PUMP_OPERATION_CONSTANT_CURRENT, 1)
        self.write(RegLoc.SETUP, setup.value)

    def setPowerMode(self):
        """Set device in constant power mode
        """
        setup = NKTSetup(self.query(RegLoc.SETUP))
        setup.setValue(SetupBits.PUMP_OPERATION_CONSTANT_CURRENT, 0)
        self.write(RegLoc.SETUP, setup.value)

    def getOutputPowerSetpoint(self):
        """Get the power mode setpoint in mW

        Returns:
            float: power mode setpoint
        """
        setpoint = self.query(RegLoc.OUTPUT_POWER_SETPOINT_mW)
        return setpoint

    def setOutputPowerSetpoint(self, power):
        """Set power mode setpoint in mW.
        Currently functioning, cause unknown.

        Args:
            power (float): power mode setpoint in mW
        """
        # not changing any settings
        self.write(RegLoc.OUTPUT_POWER_SETPOINT_mW, power)

    def getWavelengthCenter(self):
        """Get the device center wavelength in nm

        Returns:
            float: center wavelength in nm
        """
        center = self.query(RegLoc.WAVELENGTH_CENTER)
        return center

    def getWavelengthOffset(self):
        """Get the device wavelength offset setpoint in pm.

        Returns:
            float: wavelength offset setpoint in pm
        """
        offset = self.query(RegLoc.WAVELENGTH_OFFSET)
        return offset

    def setWavelengthOffset(self, offset):
        """Set the device wavelength offset setpoint in pm.

        Args:
            offset (float): wavelength offset setpoint in pm
        """
        self.write(RegLoc.WAVELENGTH_OFFSET, offset)

    def getWavelengthOffsetReadout(self):
        """Get the device readout wavelength offset setpoint in pm.

        Returns:
            float: device wavelength offset setpoint in pm
        """
        offset = self.query(RegLoc.WAVELENGTH_OFFSET_READOUT)
        return offset

    def getWavelength(self):
        """Get the device current wavelength in nm

        Returns:
            float: current wavelength in nm
        """
        center = self.getWavelengthCenter()
        offset = self.getWavelengthOffsetReadout() / 1e3 # convert to nm
        return center + offset

    def setWavelength(self, wavelength):
        """Set the device wavelength setpoint in nm

        Args:
            wavelength (int): wavelenght offset in nm
        """
        center = self.getWavelengthCenter()
        offset = int(wavelength - center)
        offset *= 1e3 # convert to pm
        self.write(RegLoc.WAVELENGTH_OFFSET, offset)

    def getWavelengthSetpoint(self):
        """Get the device wavelength setpoint in nm

        Returns:
            float: wavelength setpoint in nm
        """
        center = self.getWavelengthCenter()
        offset = self.getWavelengthOffset() / 1e3 # convert to nm
        return center + offset


    def getTemperature(self):
        """Get device temperature in C

        Returns:
            float: temperature in C
        """
        temperature = self.query(RegLoc.TEMPERATURE)
        return temperature

    def getEmission(self):
        """Module emission state

        Returns:
            bool: True = on, False = off
        """
        emission = self.query(RegLoc.EMISSION)
        return bool(emission)

    def setEmission(self, enable):
        """Set module emission state

        Args:
            enable (bool): True = on, False = off
        """
        self.write(RegLoc.EMISSION, int(enable))

    def getPower(self):
        """Power output in mW

        Returns:
            float: power output in mW
        """
        power = self.query(RegLoc.OUTPUT_POWER_mW)
        return power

    def getName(self):
        """Module name

        Returns:
            string: module name
        """
        name = self.query(RegLoc.NAME)
        return name

    def setName(self, name):
        """Set module name

        Args:
            name (str): module name
        """
        self.write(RegLoc.NAME, name)

    def getStatusBits(self):
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
        status = self.query(RegLoc.STATUS)
        return status
    
    def getStatus(self):
        """Readout device status codes

        Returns:
            list: list with current status codes
        """
        return NKTStatus(self.getStatusBits()).getStatus()
    
    def getErrorBits(self):
        """Module error bits
        0: no error
        2: interlock
        3: low voltage
        7: module temperature range
        8: module disabled

        Returns:
            int: error bits
        """
        error = self.query(RegLoc.ERROR)
        return error

    def getError(self):
        """Readout the device error codes

        Returns:
            list: list with triggered error codes
        """
        return NKTError(self.getErrorBits()).getErrors()

    def setModulation(self, enable):
        """Enable or disable wavelength modulation

        Args:
            enable (bool): True = enabled, False = disableb
        """
        self.write(RegLoc.WAVELENGTH_MODULATION, int(enable))

    def getModulation(self):
        """Get current wavelength modulation state

        Returns:
            bool: True = enabled, False = disabled
        """
        return bool(self.query(RegLoc.WAVELENGTH_MODULATION))
    
    def getModulationRange(self):
        """Module modulation range

        Returns:
            str: WIDE or NARROW
        """
        setup = NKTSetup(self.query(RegLoc.SETUP))
        return 'NARROW' if setup.getValue(SetupBits.NARROW_WAVELENGTH_MODULATION) else 'WIDE'

    def setModulationRange(self, modulation_range):
        """Set module modulation range

        Args:
            modulation_range (str): WIDE or NARROW modulation range
        """
        if modulation_range not in ['WIDE', 'NARROW']:
            logging.error("Basik setModulationRange(): invalid range" \
                            +"specified, valid entries are NARROW or WIDE")
            return

        setup = NKTModulationSetup(self.query(RegLoc.SETUP))
        modulation_range = 1 if modulation_range == 'NARROW' else 0
        setup.setValue(SetupBits.NARROW_WAVELENGTH_MODULATION, modulation_range)
    
        self.write(RegLoc.SETUP, setup.value)

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
        return constants.c.value/(center + offset)

    def getFrequencySetpoint(self):
        """Frequency setpoint in GHz

        Returns:
            float: frequency setpoint in GHz
        """
        center = self.getWavelengthCenter()
        offset = self.getWavelengthOffset() / 1e3
        return constants.c.value/(center + offset)

    def setFrequency(self, frequency):
        """Set module frequency in GHz

        Args:
            frequency (float): frequency in GHz
        """
        self.setWavelength(constants.c.value/frequency)

    def moveFrequency(self, deviation):
        """Move module frequency in GHz

        Args:
            deviation (float): frequency deviation in GHz
        """
        frequency = self.getFrequency()
        self.setWavelength(constants.c.vallue/(frequency + deviation))