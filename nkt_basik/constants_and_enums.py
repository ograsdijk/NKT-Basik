from dataclasses import dataclass
from enum import Enum

from .bits_handling import ModulationWaveform


class physicalConstants(Enum):
    c = 299792458.0  # m/s


class ModulationRange(Enum):
    WIDE = 0
    NARROW = 1


class LaserMode(Enum):
    POWER = 0
    CURRENT = 1


class ModulationCoupling(Enum):
    AC = 0
    DC = 1


class ModulationSource(Enum):
    EXTERNAL = 1
    INTERNAL = 2
    BOTH = 3


@dataclass
class WavelengthModulation:
    state: bool
    frequency: float
    amplitude: float
    offset: float
    modulation_range: ModulationRange
    modulation_source: ModulationSource
    modulation_waveform: ModulationWaveform
    coupling: ModulationCoupling
