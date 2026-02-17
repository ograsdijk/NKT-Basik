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


class BasikConnectionError(Exception):
    pass


class BasikTypeError(TypeError):
    pass


class Basik:
    """High-level API for a single NKT Basik module.

    This API uses strict enum inputs for mode and modulation configuration.
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

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _connect(self) -> None:
        """Connect to NKT basik module"""
        device_result = openPorts(self.port, 0, 0)
        if device_result != 0:
            device_result = DeviceResultTypes(device_result).split(":")[-1]
            raise BasikConnectionError(
                f"Failed to open port {self.port}: {device_result}"
            )

        device_result = deviceCreate(self.port, self.devID, 1)
        if device_result != 0:
            device_result = DeviceResultTypes(device_result).split(":")[-1]
            raise BasikConnectionError(
                f"Failed to create device on port {self.port}, devID {self.devID}: {device_result}"
            )

    def close(self) -> None:
        ret = deviceRemove(self.port, self.devID)
        if ret != 0:
            ret_result = PortResultTypes(ret).split(":")[-1]
            raise BasikConnectionError(
                f"Failed to remove device on {self.port}: {ret_result}"
            )
        ret = closePorts(self.port)
        if ret != 0:
            ret_result = PortResultTypes(ret).split(":")[-1]
            raise BasikConnectionError(
                f"Failed to close port {self.port}: {ret_result}"
            )

    def query(self, register: RegLoc, index: int = -1) -> int | float | str:
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

        if isinstance(value, memoryview):
            value = value.tobytes()

        if isinstance(value, bytearray):
            value = bytes(value)

        if isinstance(value, bytes):
            value = value.decode()

        if register.name in RegScaling.__members__ and isinstance(value, (int, float)):
            value *= RegScaling[register.name].value

        if not isinstance(value, (int, float, str)):
            raise BasikTypeError(
                f"Unsupported register value type for {register.name}: {type(value).__name__}."
            )
        return value

    def write(self, register: RegLoc, value: int | float | str, index: int = -1):
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

    def _read_int(self, register: RegLoc, index: int = -1) -> int:
        value = self.query(register, index=index)
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        raise BasikTypeError(
            f"Register {register.name} expected int-compatible value, got {type(value).__name__}."
        )

    def _read_float(self, register: RegLoc, index: int = -1) -> float:
        value = self.query(register, index=index)
        if isinstance(value, (int, float)):
            return float(value)
        raise BasikTypeError(
            f"Register {register.name} expected float-compatible value, got {type(value).__name__}."
        )

    def _read_str(self, register: RegLoc, index: int = -1) -> str:
        value = self.query(register, index=index)
        if isinstance(value, str):
            return value
        raise BasikTypeError(
            f"Register {register.name} expected string value, got {type(value).__name__}."
        )

    def _coerce_enum_value(self, value, enum_type: type, field_name: str):
        allowed_values = ", ".join(str(member.value) for member in enum_type)
        error_msg = (
            f"{field_name} must be a {enum_type.__name__} enum value or valid integer value "
            f"({allowed_values})."
        )
        if isinstance(value, enum_type):
            return value
        if isinstance(value, bool):
            raise BasikTypeError(error_msg)
        if isinstance(value, int):
            try:
                return enum_type(value)
            except ValueError:
                pass
        raise BasikTypeError(error_msg)

    @property
    def serial_number(self):
        """Module serial number

        Returns:
            str: serial number
        """
        serial = self._read_str(RegLoc.SERIAL_NUMBER)
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
        setup = NKTSetup(self._read_int(RegLoc.SETUP))
        val = setup.get_value(SetupBits.PUMP_OPERATION_CONSTANT_CURRENT)
        return LaserMode(val)

    @mode.setter
    def mode(self, mode: LaserMode | int) -> None:
        """
        Setter of the Basik laser mode, possible modes are:
        POWER -> vary current to stabilize the power
        CURRENT -> stabilize the current

        Args:
            mode (LaserMode | int): Mode enum (either POWER or CURRENT)
        """
        mode = self._coerce_enum_value(mode, LaserMode, "mode")

        setup = NKTSetup(self._read_int(RegLoc.SETUP))
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
        setpoint = self._read_float(RegLoc.OUTPUT_POWER_SETPOINT_mW)
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
        center = self._read_float(RegLoc.WAVELENGTH_CENTER)
        return center

    @property
    def wavelength_offset(self) -> float:
        """Get the device wavelength offset setpoint in pm.

        Returns:
            float: wavelength offset setpoint in pm
        """
        offset = self._read_float(RegLoc.WAVELENGTH_OFFSET)
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
        offset = self._read_float(RegLoc.WAVELENGTH_OFFSET_READOUT)
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
        temperature = self._read_float(RegLoc.TEMPERATURE)
        return temperature

    @property
    def supply_voltage(self) -> float:
        """Get device supply voltage in V.

        Returns:
            float: supply voltage in V
        """
        voltage = self._read_float(RegLoc.SUPPLY_VOLTAGE)
        return voltage

    @property
    def emission(self) -> bool:
        """Module emission state

        Returns:
            bool: True = on, False = off
        """
        emission = self._read_int(RegLoc.EMISSION)
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
        power = self._read_float(RegLoc.OUTPUT_POWER_mW)
        return power

    @property
    def name(self) -> str:
        """Module name

        Returns:
            string: module name
        """
        name = self._read_str(RegLoc.NAME)
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
        status = self._read_int(RegLoc.STATUS)
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
        error = self._read_int(RegLoc.ERROR)
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
        return self._read_int(RegLoc.SETUP)

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
        return bool(self._read_int(RegLoc.WAVELENGTH_MODULATION))

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
        setup = NKTSetup(self._read_int(RegLoc.SETUP))
        internal = setup.get_value(SetupBits.INTERNAL_WAVELENGTH_MODULATION)
        external = setup.get_value(SetupBits.EXTERNAL_WAVELENGTH_MODULATION)
        return ModulationSource(external + (internal << 1))

    @modulation_source.setter
    def modulation_source(self, source: ModulationSource | int) -> None:
        """
        Setter modulation source, either EXTERNAL, INTERNAL, BOTH

        Args:
            source (ModulationSource | int): ModulationSource enum; EXTERNAL, INTERNAL, BOTH
        """
        source = self._coerce_enum_value(source, ModulationSource, "modulation_source")

        setup = NKTSetup(self._read_int(RegLoc.SETUP))
        internal = (source.value >> 1) & 1
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
        setup = NKTSetup(self._read_int(RegLoc.SETUP))
        return ModulationRange(setup.get_value(SetupBits.NARROW_WAVELENGTH_MODULATION))

    @modulation_range.setter
    def modulation_range(self, modulation_range: ModulationRange | int) -> None:
        """Set module modulation range

        Args:
            modulation_range (ModulationRange | int): WIDE or NARROW modulation range
        """
        modulation_range = self._coerce_enum_value(
            modulation_range, ModulationRange, "modulation_range"
        )

        setup = NKTSetup(self._read_int(RegLoc.SETUP))
        setup.set_value(SetupBits.NARROW_WAVELENGTH_MODULATION, modulation_range.value)

        self.write(RegLoc.SETUP, setup.value)

    @property
    def modulation_frequency(self) -> float:
        """
        Wavelength modulation frequency

        Returns:
            float: wavelength modulation frequency in Hz
        """
        return self._read_float(RegLoc.WAVELENGTH_MODULATION_FREQUENCY, index=0)

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
        return self._read_float(RegLoc.WAVELENGTH_MODULATION_LEVEL)

    @property
    def modulation_offset(self) -> float:
        """
        Wavelength modulation offset

        Returns:
            float: wavelength modulation offset in % of full scale
        """
        return self._read_float(RegLoc.WAVELENGTH_MODULATION_OFFSET)

    @property
    def modulation_coupling(self) -> ModulationCoupling:
        """
        Modulation coupling, either AC or DC

        Returns:
            Coupling: Enum with AC (0) or DC (1)
        """
        setup = NKTSetup(self._read_int(RegLoc.SETUP))
        return ModulationCoupling(setup.get_value(SetupBits.WAVELENGTH_MODULATION_DC))

    @modulation_coupling.setter
    def modulation_coupling(self, coupling: ModulationCoupling | int):
        """
        Modulation coupling, either AC or DC

        Args:
            coupling (ModulationCoupling | int): Enum with AC (0) or DC (1)
        """
        coupling = self._coerce_enum_value(
            coupling, ModulationCoupling, "modulation_coupling"
        )

        setup = NKTSetup(self._read_int(RegLoc.SETUP))
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
        return NKTModulationSetup(
            self._read_int(RegLoc.MODULATION_SETUP)
        ).get_waveform()

    @modulation_waveform.setter
    def modulation_waveform(self, waveform: ModulationWaveform | int) -> None:
        waveform = self._coerce_enum_value(
            waveform, ModulationWaveform, "modulation_waveform"
        )
        setup = NKTModulationSetup(self._read_int(RegLoc.MODULATION_SETUP))
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
