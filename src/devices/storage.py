from typing import Dict, List, Optional, Any
from fastmcp import FastMCP


class StorageDevice:
    def __init__(self, device_id: str, name: str, mount_point: Optional[str] = None):
        self.device_id = device_id
        self.name = name
        self.mount_point = mount_point


def register_tools(app: FastMCP) -> None:
    @app.tool(
        name="list_storage_devices",
        description="List all storage devices connected to the system",
    )
    async def list_storage_devices(
        removable_only: bool = False, mounted_only: bool = False
    ) -> List[Dict[str, Any]]:
        devices = [
            {
                "device_id": "disk0",
                "name": "Internal SSD",
                "mount_point": "/",
                "removable": False,
                "size": "512GB",
            },
            {
                "device_id": "disk1",
                "name": "USB Flash Drive",
                "mount_point": "/Volumes/USB",
                "removable": True,
                "size": "32GB",
            },
            {
                "device_id": "disk2",
                "name": "External HDD",
                "mount_point": None,
                "removable": True,
                "size": "2TB",
            },
        ]

        if removable_only:
            devices = [d for d in devices if d.get("removable", False)]

        if mounted_only:
            devices = [d for d in devices if d.get("mount_point") is not None]

        return devices

    @app.tool(
        name="get_storage_info",
        description="Get detailed information about a storage device",
    )
    async def get_storage_info(device_id: str) -> Dict[str, Any]:
        return {
            "device_id": device_id,
            "name": f"Storage Device {device_id}",
            "model": "Samsung SSD 970 EVO",
            "serial": "S3X9NX0M712345",
            "size": "512GB",
            "used": "256GB",
            "available": "256GB",
            "file_system": "APFS",
            "mount_point": "/",
            "removable": False,
            "read_only": False,
        }

    @app.tool(name="mount_storage", description="Mount a storage device")
    async def mount_storage(
        device_id: str, mount_point: Optional[str] = None, read_only: bool = False
    ) -> Dict[str, Any]:
        return {
            "success": True,
            "device_id": device_id,
            "mount_point": mount_point or f"/Volumes/Device-{device_id}",
            "read_only": read_only,
        }

    @app.tool(name="unmount_storage", description="Unmount a storage device")
    async def unmount_storage(device_id: str, force: bool = False) -> Dict[str, Any]:
        return {
            "success": True,
            "device_id": device_id,
            "was_mounted": True,
            "force_applied": force,
        }
