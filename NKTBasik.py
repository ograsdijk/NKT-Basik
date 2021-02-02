import logging
import numpy as np
from scipy import constants
from bits_handling import NKTStatus, NKTError, NKTSetup, NKTModulationSetup
from dll.register_enums import RegLoc, RegTypeRead, RegScaling, RegTypeWrite, SetupBits
from dll.NKTP_DLL import DeviceResultTypes, openPorts, getAllPorts,deviceGetAllTypes, getOpenPorts, \
                        closePorts, deviceRemove, deviceCreate

def find_device_by_name(name):
    # arguments are automode and livemode
    # automode: 0 open port, 1 open and start scanning devIDs
    # livemode: 0 disables continuous monitoring, 1 enable; allows for callbacks
    # takes about 2 to 3 s
    openPorts(getAllPorts(), 1, 0)

    devices = {}
    for port in getOpenPorts().split(','):
        result_type, device_types = deviceGetAllTypes(port)
        if result_type != 0:
            device_result = DeviceResultTypes(result_type).split(':')[-1]
            logging.warning(f'find_device_by_name({name}): {device_result}')
            continue
        else:
            devices[port] = [devID for devID in range(len(device_types)) if device_types[devID] != 0]

    for com, devIDs in devices.items():
        for devID in devIDs:
            basik = NKTBasik(com, devID)
            if basik.getName() == name:
                deviceRemove(com, devID)
                closePorts(getOpenPorts())
                return com, devID
            else:
                deviceRemove(com, devID)

    closePorts(getOpenPorts())
    return None

def find_devices_by_names(names):
    # arguments are automode and livemode
    # automode: 0 open port, 1 open and start scanning devIDs
    # livemode: 0 disables continuous monitoring, 1 enable; allows for callbacks
    # takes about 2 to 3 s
    openPorts(getAllPorts(), 1, 0)

    devices = {}
    for port in getOpenPorts().split(','):
        result_type, device_types = deviceGetAllTypes(port)
        if result_type != 0:
            device_result = DeviceResultTypes(result_type).split(':')[-1]
            logging.warning(f'find_devices_by_names({names}): {device_result}')
            continue
        else:
            devices[port] = [devID for devID in range(len(device_types)) if device_types[devID] != 0]
    
    devices_by_name = {name: None for name in names}
    for com, devIDs in devices.items():
        for devID in devIDs:
            basik = NKTBasik(com, devID)
            if basik.getName() in names:
                devices_by_name[basik.getName()] = (com, devID)
            deviceRemove(com, devID)

    closePorts(getOpenPorts())
    return devices_by_name
        


class NKTBasik:
    def __init__(self, port, devID):
        self.port = port
        self.devID = devID

        openPorts(port, 0, 0)
        deviceCreate(port, devID, 1)

    def query(self, register, index = None):
        if not index:
            index = -1
        result_type, value = RegTypeRead[register.name](
                                                    self.port, 
                                                    self.devID,
                                                    register.value,
                                                    index
        )
        if result_type != 0:
            device_result = DeviceResultTypes(result_type).split(':')[-1]
            logging.warning(f'NKTBasik query({register.name}, {index}): {device_result}')
            return None

        if isinstance(value, bytes):
            value = value.decode()

        try:
            # rescale value
            value *= RegScaling[register.name].value
        except KeyError:
            pass
        return value

    def write(self, register, value, index = None):
        if not index:
            index = -1
        try:
            value /= RegScaling[register.name].value
            value = int(value)
        except KeyError:
            pass
        RegTypeWrite[register.name](
                                    self.port,
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
        serial = self.query(RegLoc.SERIAL_NUMBER)
        return serial

    def setCurrentMode(self):
        setup = NKTSetup(self.query(RegLoc.SETUP))
        setup.setValue(SetupBits.PUMP_OPERATION_CONSTANT_CURRENT, 1)
        self.write(RegLoc.SETUP, setup.value)

    def setPowerMode(self):
        setup = NKTSetup(self.query(RegLoc.SETUP))
        setup.setValue(SetupBits.PUMP_OPERATION_CONSTANT_CURRENT, 0)
        self.write(RegLoc.SETUP, setup.value)

    def setOutputPowerSetpoint(self, power):
        # not changing any settings
        self.write(RegLoc.OUTPUT_POWER_SETPOINT_mW, power)

    def getOutputPowerSetpoint(self):
        setpoint = self.query(RegLoc.OUTPUT_POWER_SETPOINT_mW)
        return setpoint

    def getWavelengthCenter(self):
        """
        Wavelength center in nm
        """
        center = self.query(RegLoc.WAVELENGTH_CENTER)
        return center

    def getWavelengthOffset(self):
        """
        Wavelength offset setpoint in pm
        """
        offset = self.query(RegLoc.WAVELENGTH_OFFSET)
        return offset

    def setWavelengthOffset(self, offset):
        self.write(RegLoc.WAVELENGTH_OFFSET, offset)

    def getWavelengthOffsetReadout(self):
        """
        Wavelength offset readout in pm
        """
        offset = self.query(RegLoc.WAVELENGTH_OFFSET_READOUT)
        return offset

    def getWavelength(self):
        """
        Wavelength in nm
        """
        center = self.getWavelengthCenter()
        offset = self.getWavelengthOffsetReadout() / 1e3 # convert to nm
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
        offset = self.getWavelengthOffset() / 1e3 # convert to nm
        return center + offset


    def getTemperature(self):
        """
        Module temperature in C
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

    def setEmission(self, state):
        """Set module emission state

        Args:
            state (bool): True = on, False = off
        """
        self.write(RegLoc.EMISSION, np.uint8(state))

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
        status = self.query(RegLoc.STATUS)
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
        error = self.query(RegLoc.ERROR)
        return error

    def setModulation(self, enable):
        self.write(RegLoc.WAVELENGTH_MODULATION, int(enable))

    def getModulation(self):
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
            logging.warning("NKTBasik setModulationRange(): invalid range" \
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
        return constants.c/(center + offset)

    def getFrequencySetpoint(self):
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