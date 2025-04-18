from typing import Optional, Union

from .bits_handling import (
    BasikError,
    BasikSetup,
    BasikStatus,
    ModulationWaveform,
    NKTError,
    NKTModulationSetup,
    NKTSetup,
    NKTStatus,
    SetupBits,
)
from .constants_and_enums import (
    LaserMode,
    ModulationCoupling,
    ModulationRange,
    ModulationSource,
    WavelengthModulation,
)
from .dll.NKTP_DLL import (
    DeviceResultTypes,
    NKTRegisterException,
    PortResultTypes,
    RegisterResultTypes,
    closePorts,
    deviceCreate,
    deviceRemove,
    openPorts,
)
from .dll.register_enums import RegLoc, RegScaling, RegTypeRead, RegTypeWrite
from .utils import frequency_to_wavelength, wavelength_to_frequency


class DeviceNotFoundError(Exception):
    def __init__(self, message=""):
        self.message = message

    def __str__(self):
        return self.message


class Basik:
    """Interface for an NKT Basik fiber seed laser from NKT Photonics

    Args:
        port (str): COM port of the seed laser
        devID (int): device ID of the seed laser

    Attributes:
        port (str)  : COM port of the seed laser
        devID (int) : device ID of the seed laser

    Methods:
        _connect()
        query(register, index)
        write(register, value, index)
        serial_number
        current_mode
        power_mode
        power_mode_setpoint
        power_mode_setpoint(power)
        wavelength_center
        wavelength_offset
        wavelength_offset(offset)
        wavelength_offset_readout
        wavelength
        wavelength(wavelength)
        wavelength_setpoint
        temperature
        emission
        emission(enable)
        name()
        name(name)
        status_bits
        status
        error_bits
        error
        setup_bits()
        setup
        modulation
        modulation(enable)
        modulation_range
        modulation_range(modulation_range)
        frequency
        frequency(frequency)
        frequency_setpoint
        move_frequency(deviation)

    """

    def __init__(self, port: str, devID: int):
        """Initialize NKT Basik module

        Args:
            port (str): COM port of the seed laser
            devID (int): device ID of the seed laser
        """
        self.port = port
        self.devID = devID

        self._connect()

    def __exit__(self, *exc):
        self.close()

    def _connect(self):
        """Connect to NKT basik module"""
        device_result = openPorts(self.port, 0, 0)
        if device_result != 0:
            device_result = DeviceResultTypes(device_result).split(":")[-1]
            raise DeviceNotFoundError(f"port {self.port}")

        device_result = deviceCreate(self.port, self.devID, 1)
        if device_result != 0:
            device_result = DeviceResultTypes(device_result).split(":")[-1]
            raise DeviceNotFoundError(f"port {self.port}, devID {self.devID}")

    def close(self):
        ret = deviceRemove(self.port, self.devID)
        if ret != 0:
            ret_result = PortResultTypes(ret).split(":")[-1]
            raise ValueError(f"port {self.port} {ret_result}")
        ret = closePorts(self.port)
        if ret != 0:
            ret_result = PortResultTypes(ret).split(":")[-1]
            raise ValueError(f"port {self.port} {ret_result}")

    def query(
        self, register: RegLoc, index: int = -1
    ) -> Optional[Union[int, float, str]]:
        """Query a register on a NKT Basik module

        Args:
            register (enum): RegLoc enum containing register locations
            index (int, optional): register index. Defaults to -1.

        Returns:
            (int, float, str): value of the register. Type depends on the
                                specified register.
        """
        register_result, value = RegTypeRead[register.name](
            self.port, self.devID, register.value, index
        )
        if register_result != 0:
            register_result = RegisterResultTypes(register_result).split(":")[-1]
            raise NKTRegisterException(
                f"Basik query({register.name}, {index}): {register_result}"
            )

        if isinstance(value, bytes):
            value = value.decode()

        try:
            # rescale value
            value *= RegScaling[register.name].value
        except KeyError:
            pass
        return value

    def write(self, register: RegLoc, value: Union[int, float, str], index: int = -1):
        """Write to a register on an NKT Basik module

        Args:
            register (enum): enum containing register locations
            value (int, float, str): value to write to register
            index (int, optional): register index. Defaults to -1.
        """
        try:
            if isinstance(value, (int, float)):
                value /= RegScaling[register.name].value
                value = int(value)
        except KeyError:
            pass
        register_result = RegTypeWrite[register.name](
            self.port, self.devID, register.value, value, index
        )
        if register_result != 0:
            register_result = RegisterResultTypes(register_result).split(":")[-1]
            raise NKTRegisterException(
                f"Basik write({register.name}, {index}): {register_result}"
            )

    @property
    def serial_number(self):
        """Module serial number

        Returns:
            str: serial number
        """
        serial = self.query(RegLoc.SERIAL_NUMBER)
        return serial

    @property
    def mode(self) -> LaserMode:
        """
        Getter of the Basik laser mode, possible modes are:
        POWER -> vary current to stabilize the power
        CURRENT -> stabilize the current

        Returns:
            Mode: Mode enum (either POWER or CURRENT)
        """
        setup = NKTSetup(self.query(RegLoc.SETUP))
        val = setup.get_value(SetupBits.PUMP_OPERATION_CONSTANT_CURRENT)
        return LaserMode(val)

    @mode.setter
    def mode(self, mode: str | LaserMode) -> None:
        """
        Setter of the Basik laser mode, possible modes are:
        POWER -> vary current to stabilize the power
        CURRENT -> stabilize the current

        Args:
            mode (str | LaserMode): Mode enum (either POWER or CURRENT)
        """
        if isinstance(mode, str):
            assert mode.casefold() in ["power", "current"]
            mode = LaserMode[mode.upper()]

        setup = NKTSetup(self.query(RegLoc.SETUP))
        setup.set_value(SetupBits.PUMP_OPERATION_CONSTANT_CURRENT, mode.value)
        self.write(RegLoc.SETUP, setup.value)

    def set_current_mode(self):
        """
        Set device in constant current mode
        """
        self.mode = LaserMode.CURRENT

    def set_power_mode(self):
        """
        Set device in constant power mode
        """
        self.mode = LaserMode.POWER

    @property
    def output_power_setpoint(self) -> float:
        """
        Get the power mode setpoint in mW

        Returns:
            float: power mode setpoint
        """
        setpoint = self.query(RegLoc.OUTPUT_POWER_SETPOINT_mW)
        return setpoint

    @output_power_setpoint.setter
    def output_power_setpoint(self, power: float):
        """
        Set power mode setpoint in mW.
        Currently functioning, cause unknown.

        Args:
            power (float): power mode setpoint in mW
        """
        # not changing any settings
        self.write(RegLoc.OUTPUT_POWER_SETPOINT_mW, power)

    @property
    def wavelength_center(self) -> float:
        """Get the device center wavelength in nm

        Returns:
            float: center wavelength in nm
        """
        center = self.query(RegLoc.WAVELENGTH_CENTER)
        return center

    @property
    def wavelength_offset(self) -> float:
        """Get the device wavelength offset setpoint in pm.

        Returns:
            float: wavelength offset setpoint in pm
        """
        offset = self.query(RegLoc.WAVELENGTH_OFFSET)
        return offset

    @wavelength_offset.setter
    def wavelength_offset(self, offset: float):
        """Set the device wavelength offset setpoint in pm.

        Args:
            offset (float): wavelength offset setpoint in pm
        """
        self.write(RegLoc.WAVELENGTH_OFFSET, offset)

    @property
    def wavelength_offset_readout(self) -> float:
        """Get the device readout wavelength offset setpoint in pm.

        Returns:
            float: device wavelength offset setpoint in pm
        """
        offset = self.query(RegLoc.WAVELENGTH_OFFSET_READOUT)
        return offset

    @property
    def wavelength(self) -> float:
        """Get the device current wavelength in nm

        Returns:
            float: current wavelength in nm
        """
        center = self.wavelength_center
        offset = self.wavelength_offset_readout / 1e3  # convert to nm
        return center + offset

    @property
    def wavelength_setpoint(self) -> float:
        """Get the device wavelength setpoint in nm

        Returns:
            float: wavelength setpoint in nm
        """
        center = self.wavelength_center
        offset = self.wavelength_offset / 1e3  # convert to nm
        return center + offset

    @wavelength_setpoint.setter
    def wavelength_setpoint(self, wavelength: float) -> None:
        """Set the device wavelength setpoint in nm

        Args:
            wavelength (int): wavelenght offset in nm
        """
        center = self.wavelength_center
        offset = wavelength - center
        offset *= 1e3  # convert to pm
        self.write(RegLoc.WAVELENGTH_OFFSET, offset)

    @property
    def temperature(self) -> float:
        """Get device temperature in C

        Returns:
            float: temperature in C
        """
        temperature = self.query(RegLoc.TEMPERATURE)
        return temperature

    @property
    def emission(self) -> bool:
        """Module emission state

        Returns:
            bool: True = on, False = off
        """
        emission = self.query(RegLoc.EMISSION)
        return bool(emission)

    @emission.setter
    def emission(self, enable: bool) -> None:
        """Set module emission state

        Args:
            enable (bool): True = on, False = off
        """
        self.write(RegLoc.EMISSION, int(enable))

    @property
    def power(self) -> float:
        """Power output in mW

        Returns:
            float: power output in mW
        """
        power = self.query(RegLoc.OUTPUT_POWER_mW)
        return power

    @property
    def name(self) -> str:
        """Module name

        Returns:
            string: module name
        """
        name = self.query(RegLoc.NAME)
        return name

    @name.setter
    def name(self, name: str) -> None:
        """Set module name

        Args:
            name (str): module name
        """
        self.write(RegLoc.NAME, name)

    @property
    def status_bits(self) -> int:
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

    @property
    def status(self) -> BasikStatus:
        """Readout device status codes

        Returns:
            BasikStatus: dataclass with the status bits fields
        """
        return NKTStatus(self.status_bits).get_status()

    @property
    def error_bits(self) -> int:
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

    @property
    def error(self) -> BasikError:
        """Readout the device error codes

        Returns:
            list: list with triggered error codes
        """
        return NKTError(self.error_bits).get_errors()

    @property
    def setup_bits(self) -> int:
        """Module setup bits

        Returns:
            int: setup bits
        """
        return self.query(RegLoc.SETUP)

    @property
    def setup(self) -> BasikSetup:
        """Readout module setup codes

        Returns:
            BasikSetup: dataclass with the setup fields and status
        """
        return NKTSetup(self.setup_bits).get_setup()

    @property
    def modulation(self) -> bool:
        """Get current wavelength modulation state

        Returns:
            bool: True = enabled, False = disabled
        """
        return bool(self.query(RegLoc.WAVELENGTH_MODULATION))

    @modulation.setter
    def modulation(self, enable: bool) -> None:
        """Enable or disable wavelength modulation

        Args:
            enable (bool): True = enabled, False = disabled
        """
        self.write(RegLoc.WAVELENGTH_MODULATION, int(enable))

    @property
    def modulation_source(self) -> ModulationSource:
        """
        Modulation source, either EXTERNAL, INTERNAL, BOTH

        Returns:
            ModulationSource: ModulationSource enum; NA, EXTERNAL, INTERNAL, BOTH
        """
        setup = NKTSetup(int(self.query(RegLoc.SETUP)))
        internal = setup.get_value(SetupBits.INTERNAL_WAVELENGTH_MODULATION)
        external = setup.get_value(SetupBits.EXTERNAL_WAVELENGTH_MODULATION)
        return ModulationSource(external + (internal << 1))

    @modulation_source.setter
    def modulation_source(self, source: str | ModulationSource) -> None:
        """
        Setter modulation source, either EXTERNAL, INTERNAL, BOTH

        Args:
            source (str | ModulationSource): ModulationSource enum; EXTERNAL, INTERNAL, BOTH
        """
        if isinstance(source, str):
            assert source.casefold() in ["external", "internal", "both"]
            source = ModulationSource[source.upper()]
        setup = NKTSetup(self.query(RegLoc.SETUP))
        internal = source.value & 2
        external = source.value & 1
        setup.set_value(SetupBits.INTERNAL_WAVELENGTH_MODULATION, internal)
        setup.set_value(SetupBits.EXTERNAL_WAVELENGTH_MODULATION, external)
        self.write(RegLoc.SETUP, setup.value)

    @property
    def modulation_range(self) -> ModulationRange:
        """Module modulation range

        Returns:
            ModulationRange: WIDE or NARROW modulation range
        """
        setup = NKTSetup(self.query(RegLoc.SETUP))
        return ModulationRange(setup.get_value(SetupBits.NARROW_WAVELENGTH_MODULATION))

    @modulation_range.setter
    def modulation_range(self, modulation_range: str | ModulationRange) -> None:
        """Set module modulation range

        Args:
            modulation_range (str | ModulationRange): WIDE or NARROW modulation range
        """
        if isinstance(modulation_range, str):
            assert modulation_range.casefold() in ["wide", "lower"]
            modulation_range = ModulationRange[modulation_range.upper()]

        setup = NKTModulationSetup(self.query(RegLoc.MODULATION_SETUP))
        setup.set_value(SetupBits.NARROW_WAVELENGTH_MODULATION, modulation_range.value)

        self.write(RegLoc.SETUP, setup.value)

    @property
    def modulation_frequency(self) -> float:
        """
        Wavelength modulation frequency

        Returns:
            float: wavelength modulation frequency in Hz
        """
        return self.query(RegLoc.WAVELENGTH_MODULATION_FREQUENCY, index=0)

    @modulation_frequency.setter
    def modulation_frequency(self, frequency: float) -> None:
        """
        Set wavelength modulation frequency

        Args:
            float: wavelength modulation frequency in Hz

        """
        self.write(RegLoc.WAVELENGTH_MODULATION_FREQUENCY, frequency, index=0)

    @property
    def modulation_amplitude(self) -> float:
        """
        Wavelength modulation amplitude

        Returns:
            float: wavelength modulation amplitude in % of full scale
        """
        return self.query(RegLoc.WAVELENGTH_MODULATION_LEVEL)

    @property
    def modulation_offset(self) -> float:
        """
        Wavelength modulation offset

        Returns:
            float: wavelength modulation offset in % of full scale
        """
        return self.query(RegLoc.WAVELENGTH_MODULATION_OFFSET)

    @property
    def modulation_coupling(self) -> ModulationCoupling:
        """
        Modulation coupling, either AC or DC

        Returns:
            Coupling: Enum with AC (0) or DC (1)
        """
        setup = NKTSetup(self.query(RegLoc.SETUP))
        return ModulationCoupling(setup.get_value(SetupBits.WAVELENGTH_MODULATION_DC))

    @modulation_coupling.setter
    def modulation_coupling(self, coupling: str | ModulationCoupling):
        """
        Modulation coupling, either AC or DC

        Args:
            coupling (str | Coupling): Enum with AC (0) or DC (1)
        """
        if isinstance(coupling, str):
            assert coupling.casefold() in ["ac", "dc"]
            coupling = ModulationCoupling[coupling.upper()]

        setup = NKTSetup(self.query(RegLoc.SETUP))
        setup.set_value(SetupBits.WAVELENGTH_MODULATION_DC, coupling.value)
        self.write(RegLoc.SETUP, setup.value)

    @property
    def modulation_waveform(self) -> ModulationWaveform:
        """
        Wavelength modulation waveform

        Returns:
            ModulationWaveform: Enum with the modulation waveform; SINE, TRIANGLE,
                                SAWTOOTH, INVERSE_SAWTOOTH
        """
        return NKTModulationSetup(self.query(RegLoc.MODULATION_SETUP)).get_waveform()

    @modulation_waveform.setter
    def modulation_waveform(self, waveform: str | ModulationWaveform) -> None:
        if isinstance(waveform, str):
            assert waveform.casefold() in [
                "sine",
                "triangle",
                "sawtooth",
                "inverse_sawtooth",
            ]
        setup = NKTModulationSetup(self.query(RegLoc.MODULATION_SETUP))
        setup.set_waveform(waveform)
        self.write(RegLoc.MODULATION_SETUP, setup.value)

    @property
    def wavelength_modulation(self) -> WavelengthModulation:
        return WavelengthModulation(
            self.modulation,
            self.modulation_frequency,
            self.modulation_amplitude,
            self.modulation_offset,
            self.modulation_range,
            self.modulation_source,
            self.modulation_waveform,
            self.modulation_coupling,
        )

    #############################################
    # Some convenience functions
    #############################################

    @property
    def frequency(self) -> float:
        """Frequency in GHz

        Returns:
            float: frequency in GHz
        """
        center = self.wavelength_center
        offset = self.wavelength_offset_readout / 1e3
        return round(wavelength_to_frequency(center + offset), 4)

    @property
    def frequency_setpoint(self) -> float:
        """Frequency setpoint in GHz

        Returns:
            float: frequency setpoint in GHz
        """
        center = self.wavelength_center
        offset = self.wavelength_offset / 1e3
        return round(wavelength_to_frequency(center + offset), 4)

    @frequency_setpoint.setter
    def frequency_setpoint(self, frequency: float) -> None:
        """Set module frequency in GHz

        Args:
            frequency (float): frequency in GHz
        """
        self.wavelength_setpoint = round(frequency_to_wavelength(frequency), 3)

    def move_frequency(self, deviation: float) -> None:
        """Move module frequency in GHz

        Args:
            deviation (float): frequency deviation in GHz
        """
        frequency = self.frequency_setpoint
        self.wavelength_setpoint = round(
            frequency_to_wavelength(frequency + deviation), 3
        )
