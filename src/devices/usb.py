from typing import Dict, List, Any
from fastmcp import FastMCP


class USBDevice:
    def __init__(self, device_id: str, name: str):
        self.device_id = device_id
        self.name = name


def register_tools(app: FastMCP) -> None:
    @app.tool(
        name="list_usb_devices",
        description="List all USB devices connected to the system",
    )
    async def list_usb_devices() -> List[Dict[str, Any]]:
        devices = [
            {
                "device_id": "usb0",
                "name": "SanDisk Ultra USB 3.0",
                "type": "Mass Storage",
                "vendor_id": "0781",
                "product_id": "5581",
            },
            {
                "device_id": "usb1",
                "name": "Logitech Webcam C920",
                "type": "Video",
                "vendor_id": "046d",
                "product_id": "082d",
            },
            {
                "device_id": "usb2",
                "name": "Keyboard",
                "type": "HID",
                "vendor_id": "05ac",
                "product_id": "024f",
            },
        ]
        return devices

    @app.tool(
        name="get_usb_device_info",
        description="Get detailed information about a USB device",
    )
    async def get_usb_device_info(device_id: str) -> Dict[str, Any]:
        return {
            "device_id": device_id,
            "name": f"USB Device {device_id}",
            "type": "Mass Storage",
            "vendor_id": "0781",
            "product_id": "5581",
            "vendor_name": "SanDisk",
            "serial_number": "4C531001241120116131",
            "bus_number": "1",
            "port_number": "2",
            "speed": "SuperSpeed (5 Gbps)",
        }

    @app.tool(name="eject_usb_device", description="Safely eject a USB device")
    async def eject_usb_device(device_id: str, force: bool = False) -> Dict[str, Any]:
        return {
            "success": True,
            "device_id": device_id,
            "force_applied": force,
            "message": f"Device {device_id} successfully ejected.",
        }

    @app.tool(
        name="get_usb_events",
        description="Get recent USB connection/disconnection events",
    )
    async def get_usb_events(limit: int = 10) -> List[Dict[str, Any]]:
        events = [
            {
                "timestamp": "2025-05-23T12:30:45",
                "type": "connection",
                "device_id": "usb0",
                "device_name": "SanDisk Ultra USB 3.0",
            },
            {
                "timestamp": "2025-05-23T11:45:22",
                "type": "disconnection",
                "device_id": "usb3",
                "device_name": "External Hard Drive",
            },
        ]
        return events[:limit]
