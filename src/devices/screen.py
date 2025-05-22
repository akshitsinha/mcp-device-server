from typing import Dict, List, Optional, Any
from fastmcp import FastMCP


class Screen:
    def __init__(self, device_id: str, name: str):
        self.device_id = device_id
        self.name = name


def register_tools(app: FastMCP) -> None:
    @app.tool(
        name="list_displays", description="List all displays connected to the system"
    )
    async def list_displays() -> List[Dict[str, Any]]:
        displays = [
            {
                "device_id": "display0",
                "name": "Built-in Retina Display",
                "resolution": "2560x1600",
                "is_primary": True,
            },
            {
                "device_id": "display1",
                "name": "External HDMI Monitor",
                "resolution": "3840x2160",
                "is_primary": False,
            },
        ]
        return displays

    @app.tool(name="capture_screen", description="Capture a screenshot from a display")
    async def capture_screen(
        device_id: Optional[str] = None,
        save_path: Optional[str] = None,
        region: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "success": True,
            "file_path": save_path or "/tmp/mcp-peripherals/screenshot.png",
            "resolution": region or "Full Screen (2560x1600)",
            "timestamp": "2025-05-23T12:34:56",
            "device_id": device_id or "display0",
        }

    @app.tool(name="record_screen", description="Start recording a screen")
    async def record_screen(
        device_id: Optional[str] = None,
        save_path: Optional[str] = None,
        region: Optional[str] = None,
        fps: int = 30,
        audio: bool = False,
    ) -> Dict[str, Any]:
        return {
            "success": True,
            "recording_id": "screen123456",
            "file_path": save_path or "/tmp/mcp-peripherals/screen_recording.mp4",
            "start_time": "2025-05-23T12:34:56",
            "device_id": device_id or "display0",
            "region": region or "Full Screen",
            "fps": fps,
            "with_audio": audio,
        }

    @app.tool(name="stop_screen_recording", description="Stop recording a screen")
    async def stop_screen_recording(recording_id: str) -> Dict[str, Any]:
        return {
            "success": True,
            "recording_id": recording_id,
            "file_path": "/tmp/mcp-peripherals/screen_recording.mp4",
            "duration": "00:02:34",
            "file_size": "42.7 MB",
            "resolution": "2560x1600",
        }
