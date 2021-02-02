# NKT-basik
Version 0.1

Interface for [NKT Photonics Basik fiber seed laser](https://www.nktphotonics.com/lasers-fibers/product/koheras-basik-low-noise-single-frequency-oem-laser-modules/), only tested with a Y10 model.  
Consists of a class Basik which has the methods to modify wavelength, frequency, modulation, etc.

## Install
To use the package install with `python setup.py install`

## Code Example

```Python
from NKTBasik import Basik

device = Basik('COM4', 1)

# get the wavelength in nm 
print(f'Device wavelength: {device.getWavelength()} nm')

# get the frequency in GHz
print(f'Device frequency: {device.getFrequency():.4f} GHz')

# get the temperature in C
print(f'Device temperature: {device.getTemperature():.1f} C')

# set the wavelength setpoint in nm
print('Setting the wavelength to 1086.77 nm')
device.setWavelength(wavelength = 1086.77)

# get the wavelength in nm 
print(f'Device wavelength: {device.getWavelength()} nm')

# enable emission
print('Enable emission')
device.setEmission(enable = True)

# enable wavelength modulation
device.setModulation(enable = True)

# get device errors
print('Errors:',device.getError())

# get device status
print('Status:',device.getStatus())

# disable emission
print('Disable emission')
device.setEmission(enable = False)

# get device status
print('Status:',device.getStatus())
```

## TODO
* more testing
* add tests
