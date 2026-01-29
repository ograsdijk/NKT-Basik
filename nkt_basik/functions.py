import logging
from typing import Dict, Optional, Sequence, Tuple

from .dll.NKTP_DLL import (
    DeviceResultTypes,
    closePorts,
    deviceGetAllTypes,
    getAllPorts,
    getOpenPorts,
    openPorts,
)
from .module import Basik


def find_all_devices() -> Optional[Tuple[Tuple[str, int]]]:
    """
    Find all connected Basik modules

    Returns:
        Optional[Tuple[Tuple[str, int]]]: tuple of tuples with the com port and devID
    """
    openPorts(getAllPorts(), 1, 0)

    devices = {}
    try:
        for port in filter(None, getOpenPorts().split(",")):
            device_result, device_types = deviceGetAllTypes(port)
            if device_result != 0:
                _device_result = DeviceResultTypes(device_result).split(":")[-1]
                logging.warning(f"find_all_devices: {_device_result}")
                continue
            else:
                devices[port] = [
                    devID
                    for devID in range(len(device_types))
                    if device_types[devID] != 0
                ]
    finally:
        closePorts(getOpenPorts())

    if len(devices) > 0:
        return tuple(
            (port, devID) for port, devIDs in devices.items() for devID in devIDs
        )
    return None


def find_device_by_name(
    name: str, ports: Optional[Sequence[str]] = None
) -> Optional[Tuple[str, int]]:
    """Find Basik module com port and device id by checking the user modifiable
    text field

    Args:
        name (str)      : device
        ports (list)    : list port COM ports to look at, if None tries all

    Returns:
        tuple: (com, devID) or None if no device that matches found
    """
    # arguments are automode and livemode
    # automode: 0 open port, 1 open and start scanning devIDs
    # livemode: 0 disables continuous monitoring, 1 enable; allows for callbacks
    # takes about 2 to 3 s
    if not ports:
        openPorts(getAllPorts(), 1, 0)
    else:
        openPorts(",".join(ports), 1, 0)

    devices = {}
    try:
        for port in filter(None, getOpenPorts().split(",")):
            device_result, device_types = deviceGetAllTypes(port)
            if device_result != 0:
                _device_result = DeviceResultTypes(device_result).split(":")[-1]
                logging.warning(f"find_device_by_name({name}): {_device_result}")
                continue
            else:
                devices[port] = [
                    devID
                    for devID in range(len(device_types))
                    if device_types[devID] != 0
                ]
    finally:
        closePorts(getOpenPorts())

    for com, devIDs in devices.items():
        for devID in devIDs:
            basik = Basik(com, devID)
            if basik.name == name:
                basik.close()
                return com, devID
            else:
                basik.close()
    return None


def find_devices_by_names(
    names: Sequence[str], ports: Optional[Sequence[str]] = None
) -> Dict[str, Optional[Tuple[str, int]]]:
    """Find Basik module com ports and device ids by checking the user
    modifiable text field for each of the supplied names

    Args:
        names (list): list with devices names
        ports (list): list port COM ports to look at, if None tries all

    Returns:
        dict: dictionary with a (com, devID) tuple for each name, or None if
                device not found
    """
    # arguments are automode and livemode
    # automode: 0 open port, 1 open and start scanning devIDs
    # livemode: 0 disables continuous monitoring, 1 enable; allows for callbacks
    # takes about 2 to 3 s
    if not ports:
        openPorts(getAllPorts(), 1, 0)
    else:
        openPorts(",".join(ports), 1, 0)

    devices = {}
    try:
        for port in filter(None, getOpenPorts().split(",")):
            device_result, device_types = deviceGetAllTypes(port)
            if device_result != 0:
                _device_result = DeviceResultTypes(device_result).split(":")[-1]
                logging.warning(f"find_devices_by_names({names}): {_device_result}")
                continue
            else:
                devices[port] = [
                    devID
                    for devID in range(len(device_types))
                    if device_types[devID] != 0
                ]
    finally:
        closePorts(getOpenPorts())

    devices_by_name: Dict[str, Optional[Tuple[str, int]]] = {
        name: None for name in names
    }
    for com, devIDs in devices.items():
        for devID in devIDs:
            basik = Basik(com, devID)
            if basik.name in names:
                devices_by_name[basik.name] = (com, devID)
            basik.close()

    return devices_by_name
