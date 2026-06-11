import logging
from dataclasses import dataclass
from typing import Sequence

from .dll.NKTP_DLL import (
    DeviceResultTypes,
    PortResultTypes,
    closePorts,
    deviceGetAllTypes,
    getAllPorts,
    getOpenPorts,
    openPorts,
)
from .module import Basik


@dataclass(frozen=True)
class DeviceRef:
    port: str
    dev_id: int
    name: str


def _discover_raw(ports: Sequence[str] | None = None) -> list[tuple[str, int]]:
    target_ports = getAllPorts() if ports is None else ",".join(ports)
    previously_open = set(filter(None, getOpenPorts().split(",")))
    open_result = openPorts(target_ports, 1, 0)
    if open_result != 0:
        _open_result = PortResultTypes(open_result).split(":")[-1]
        logging.warning(f"discover_devices: {_open_result}")
        return []

    discovered: list[tuple[str, int]] = []
    try:
        opened_ports = set(filter(None, getOpenPorts().split(",")))
        discovered_ports = opened_ports - previously_open
        for port in sorted(discovered_ports):
            device_result, device_types = deviceGetAllTypes(port)
            if device_result != 0:
                _device_result = DeviceResultTypes(device_result).split(":")[-1]
                logging.warning(f"discover_devices: {_device_result}")
                continue

            discovered.extend(
                (port, dev_id)
                for dev_id in range(len(device_types))
                if device_types[dev_id] != 0
            )
    finally:
        ports_to_close = set(filter(None, getOpenPorts().split(","))) - previously_open
        if ports_to_close:
            closePorts(",".join(sorted(ports_to_close)))

    return discovered


def find_devices(ports: Sequence[str] | None = None) -> list[DeviceRef]:
    """Discover all devices and return typed descriptors.

    Returns:
        list[DeviceRef]: list of discovered devices, empty if none are found.
    """

    devices: list[DeviceRef] = []
    for port, dev_id in _discover_raw(ports=ports):
        with Basik(port, dev_id) as basik:
            devices.append(DeviceRef(port=port, dev_id=dev_id, name=basik.name))
    return devices


def find_devices_by_names(
    names: Sequence[str], ports: Sequence[str] | None = None
) -> dict[str, list[DeviceRef]]:
    """Discover devices and group matches by requested name.

    Returns:
        dict[str, list[DeviceRef]]: mapping with empty lists for names that are not found.
    """

    grouped: dict[str, list[DeviceRef]] = {name: [] for name in names}
    target_names = set(names)

    for device in find_devices(ports=ports):
        if device.name in target_names:
            grouped[device.name].append(device)

    return grouped


def find_device(name: str, ports: Sequence[str] | None = None) -> list[DeviceRef]:
    """Discover all devices that match a given name."""

    return find_devices_by_names([name], ports=ports)[name]
