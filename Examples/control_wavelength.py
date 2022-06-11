import time
from typing import Optional
from dataclasses import dataclass
from NKTBasik import Basik


def check_stabilized(
    device: Basik,
    measurement: str = "wavelength",
    tolerance: float = 1e-3,
    dt: float = 1.0,
    dt_stable: float = 5.0,
    verbose: bool = True,
):
    units = {"wavelength": "nm", "frequency": "Ghz"}
    setpoint = getattr(device, f"{measurement}_setpoint")
    # wait to stabilize
    counter = 0
    while True:
        wl = getattr(device, measurement)
        if verbose:
            print(
                f"{measurement} = {wl:.4f} {units[measurement]}; Δ = {setpoint-wl:.4f} "
                f"{units[measurement]}"
            )
        if abs(wl - setpoint) < tolerance:
            counter += 1
            if dt * counter >= dt_stable:
                break
        else:
            counter = 0
        time.sleep(1)
    if verbose:
        print(
            f"reached setpoint with tolerance {tolerance:.2e}; stable for "
            f"{dt*counter} seconds"
        )


device = Basik("COM6", 1)

# get the temperature in C
print(f"Device name: {device.name}")
print(f"Device temperature: {device.temperature:.1f} C")
print(f"==" * 25)

wavelength = 1086.80

# set the wavelength in nm
if device.wavelength_setpoint != wavelength:
    device.wavelength = wavelength

    # wait to stabilize
    check_stabilized(device, "wavelength")


# move frequency up by 10 GHz
Δfrequency = 20
frequency = device.frequency
step_size = 10  # GHz

print(f"original frequency = {device.frequency:.4f} GHz")
print(f"setpoint frequency = {device.frequency + Δfrequency:.4f} GHz")
print(f"==" * 25)
for _ in range(int(Δfrequency / step_size)):
    device.move_frequency(step_size)
    time.sleep(5)

check_stabilized(device, "frequency", tolerance=1e-1)
