# NKT-basik

Python interface for [NKT Photonics Basik fiber seed lasers](https://www.nktphotonics.com/lasers-fibers/product/koheras-basik-low-noise-single-frequency-oem-laser-modules/).

## Install

```bash
pip install nkt_basik
```

## API design

The package now exposes one high-level API layer:

- `Basik`
- `LaserMode`
- `ModulationRange`
- `ModulationSource`
- `ModulationCoupling`
- `ModulationWaveform`
- `DeviceRef`
- `find_devices()` / `find_device()` / `find_devices_by_names()`

Mode and modulation setters require enum inputs.

## Quickstart

```python
from nkt_basik import (
	Basik,
	LaserMode,
	ModulationCoupling,
	ModulationRange,
	ModulationSource,
	ModulationWaveform,
)

device = Basik("COM4", 1)

print(f"Name: {device.name}")
print(f"Wavelength: {device.wavelength:.4f} nm")
print(f"Frequency: {device.frequency:.4f} GHz")

device.mode = LaserMode.POWER
device.emission = True

device.modulation = True
device.modulation_source = ModulationSource.BOTH
device.modulation_range = ModulationRange.NARROW
device.modulation_coupling = ModulationCoupling.DC
device.modulation_waveform = ModulationWaveform.SINE
device.modulation_frequency = 100.0

device.frequency_setpoint = 275.1000

print(device.status)
print(device.error)

device.close()
```

Context manager usage is optional:

```python
with Basik("COM4", 1) as device:
	print(device.name)
```

## Discovery

```python
from nkt_basik import find_device, find_devices, find_devices_by_names

all_devices = find_devices()
named = find_device("seed-a")
grouped = find_devices_by_names(["seed-a", "seed-b"])
```

`find_devices()` always returns a list (possibly empty).

## Errors

- Connection failures raise `nkt_basik.module.BasikConnectionError`.
- Bad API value types raise `nkt_basik.module.BasikTypeError`.
- Register communication errors raise `NKTRegisterException`.
