from .constants_and_enums import physicalConstants


def wavelength_to_frequency(wavelength: float) -> float:
    """
    Convert wavelength in nm to frequency in GHz

    Args:
        wavelength (float): wavelength in nm

    Returns:
        float: frequency in GHz
    """
    return physicalConstants.c.value / wavelength


def frequency_to_wavelength(frequency: float) -> float:
    """
    Convert frequency in GHz to wavelength in nm

    Args:
        frequency (float): frequency in GHz

    Returns:
        float: wavelength in nm
    """
    return physicalConstants.c.value / frequency
