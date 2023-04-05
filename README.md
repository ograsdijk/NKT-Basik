# NKT-basik
Version 0.1

Interface for [NKT Photonics Basik fiber seed laser](https://www.nktphotonics.com/lasers-fibers/product/koheras-basik-low-noise-single-frequency-oem-laser-modules/), only tested with a Y10 model.  
Consists of a class Basik which has the methods to modify wavelength, frequency, modulation, etc.

## Install
To use the package install with `pip install nkt_basik` or install from source.

## Code Example

```Python
from nkt_basik import Basik

device = Basik('COM4', 1)

# get the wavelength in nm 
print(f'Device wavelength: {device.wavelength} nm')

# get the frequency in GHz
print(f'Device frequency: {device.frequency:.4f} GHz')

# get the temperature in C
print(f'Device temperature: {device.temperature:.1f} C')

# set the wavelength setpoint in nm
print('Setting the wavelength to 1086.77 nm')
device.wavelength = 1086.77

# get the wavelength in nm 
print(f'Device wavelength: {device.wavelength} nm')

# enable emission
print('Enable emission')
device.emission = True

# enable wavelength modulation
device.modulation = True

# get device errors
print('Errors:',device.error)

# get device status
print('Status:',device.status)

# disable emission
print('Disable emission')
device.emission = False

# get device status
print('Status:',device.status)
```

## TODO
* more testing
* add tests
