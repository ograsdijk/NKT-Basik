# NKT-basik
Version 0.1

Interface for NKT Photonics Basik fiber seed laser.
Consists of a class Basik which has the methods to modify wavelength, frequency, modulation, etc.

## Install
To use the package install with `python setup.py install`

## Code Example

```Python
from NKTBasik import Basik

device = Basik('COM4', 1)

# get the wavelength in nm 
print(f'{device.getWavelength()} nm')

# get the frequency in GHz
print(f'{device.getFrequency()} GHz')

# get the temperature in C
print(f'{device.getTemperature()} C')

# set the wavelength setpoint in nm
device.setWavelengthSetpoint(wavelength = 1086.7)

# enable emission
device.setEmission(enable = True)

# enable wavelength modulation
device.setModulation(enable = True)

# disable emission
device.getEmission(enable = False)

# get device errors
print(device.getErrors())

# get device status
print(device.getStatus())

```