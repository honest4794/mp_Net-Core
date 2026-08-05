"""
network_drv.py — 網路管理 (無獨立 GPIO)

產物: bus.register_service("network_manager", nm)
"""
from lib.sys_bus import bus
from lib.network_manager import NetworkManager


def init_network(sysbus=None):
    sysbus = sysbus or bus
    nm = sysbus.get_service("network_manager")
    if nm is not None:
        return nm
    nm = NetworkManager(sysbus)
    sysbus.register_service("network_manager", nm)
    return nm
