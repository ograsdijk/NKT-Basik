import logging
from .module import Basik
from .dll.NKTP_DLL import DeviceResultTypes, openPorts, getAllPorts, \
                    deviceGetAllTypes, getOpenPorts, closePorts, deviceRemove


def find_device_by_name(name):
    """Find Basik module com port and device id by checking the user modifiable
    text field

    Args:
        name (str): device

    Returns:
        tuple: (com, devID) or None if no device that matches found
    """
    # arguments are automode and livemode
    # automode: 0 open port, 1 open and start scanning devIDs
    # livemode: 0 disables continuous monitoring, 1 enable; allows for callbacks
    # takes about 2 to 3 s
    openPorts(getAllPorts(), 1, 0)

    devices = {}
    for port in getOpenPorts().split(','):
        device_result, device_types = deviceGetAllTypes(port)
        if device_result != 0:
            device_result = DeviceResultTypes(device_result).split(':')[-1]
            logging.warning(f'find_device_by_name({name}): {device_result}')
            continue
        else:
            devices[port] = [devID for devID in range(len(device_types)) if device_types[devID] != 0]

    for com, devIDs in devices.items():
        for devID in devIDs:
            basik = Basik(com, devID)
            if basik.getName() == name:
                deviceRemove(com, devID)
                closePorts(getOpenPorts())
                return com, devID
            else:
                deviceRemove(com, devID)

    closePorts(getOpenPorts())
    return None

def find_devices_by_names(names):
    """Find Basik module com ports and device ids by checking the user 
    modifiable text field for each of the supplied names

    Args:
        names (list): list with devices names

    Returns:
        dict: dictionary with a (com, devID) tuple for each name, or None if 
                device not found
    """ 
    # arguments are automode and livemode
    # automode: 0 open port, 1 open and start scanning devIDs
    # livemode: 0 disables continuous monitoring, 1 enable; allows for callbacks
    # takes about 2 to 3 s
    openPorts(getAllPorts(), 1, 0)

    devices = {}
    for port in getOpenPorts().split(','):
        device_result, device_types = deviceGetAllTypes(port)
        if device_result != 0:
            device_result = DeviceResultTypes(device_result).split(':')[-1]
            logging.warning(f'find_devices_by_names({names}): {device_result}')
            continue
        else:
            devices[port] = [devID for devID in range(len(device_types)) if device_types[devID] != 0]
    
    devices_by_name = {name: None for name in names}
    for com, devIDs in devices.items():
        for devID in devIDs:
            basik = Basik(com, devID)
            if basik.getName() in names:
                devices_by_name[basik.getName()] = (com, devID)
            deviceRemove(com, devID)

    closePorts(getOpenPorts())
    return devices_by_name