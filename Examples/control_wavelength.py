import time

from rich.console import Console

from nkt_basik import Basik


def check_stabilized(
    device: Basik,
    measurement: str = "wavelength",
    tolerance: float = 1e-3,
    dt: float = 1.0,
    dt_stable: float = 5.0,
    progress: bool = True,
):
    if progress:
        console = Console()
    else:

        class dummy:
            class status:
                def __init__(self, message: str, *args, **kwargs):
                    pass

                def __enter__(self):
                    return None

                def __exit__(self, *exc):
                    return None

        console = dummy()  # type: ignore

    units = {"wavelength": "nm", "frequency": "Ghz"}
    setpoint = getattr(device, f"{measurement}_setpoint")

    unit = units[measurement]

    # wait to stabilize
    counter = 0
    with console.status(
        f"Waiting for {measurement} to stabilize", spinner="dots"
    ) as status:
        while True:
            wl = getattr(device, measurement)
            within_limits = abs(wl - setpoint) < tolerance
            if within_limits:
                color = "green"
            else:
                color = "red"
            if progress:
                status.update(
                    f"Waiting for {measurement} to stabilize\n   set ="
                    f" {setpoint:.4f} {unit}, act = [{color}]{wl:.2f} {unit}[/{color}],"
                    f" Δ = [{color}]{setpoint - wl:.4f} {unit}[/{color}]"
                )
            if within_limits:
                counter += 1
                if dt * counter >= dt_stable:
                    break
            else:
                counter = 0
            time.sleep(dt)
        if progress:
            console.print(
                f"reached setpoint with tolerance {tolerance:.2e} {unit}; stable for "
                f"{dt*counter} seconds"
            )


device = Basik("COM6", 1)

# get the temperature in C
print(f"Device name: {device.name}")
print(f"Device temperature: {device.temperature:.1f} C")
print("==" * 25)

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
print("==" * 25)
for _ in range(int(Δfrequency / step_size)):
    device.move_frequency(step_size)
    time.sleep(5)

check_stabilized(device, "frequency", tolerance=1e-1)
