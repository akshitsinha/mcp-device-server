from typing import Dict, List, Optional, Any
from fastmcp import FastMCP


class Camera:
    def __init__(self, device_id: str, name: str):
        self.device_id = device_id
        self.name = name


def register_tools(app: FastMCP) -> None:
    @app.tool(
        name="list_cameras", description="List all cameras connected to the system"
    )
    async def list_cameras() -> List[Dict[str, str]]:
        cameras = [
            {"device_id": "cam0", "name": "Integrated Camera"},
            {"device_id": "cam1", "name": "External USB Camera"},
        ]
        return cameras

    @app.tool(
        name="get_camera_info", description="Get detailed information about a camera"
    )
    async def get_camera_info(device_id: str) -> Dict[str, Any]:
        return {
            "device_id": device_id,
            "name": f"Camera {device_id}",
            "resolution": "1920x1080",
            "connection_type": "USB",
            "status": "available",
        }

    @app.tool(name="capture_image", description="Capture an image from a camera")
    async def capture_image(
        device_id: str,
        resolution: Optional[str] = None,
        save_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "success": True,
            "file_path": save_path or "/tmp/mcp-peripherals/captured_image.jpg",
            "image_size": "2.1 MB",
            "resolution": resolution or "1920x1080",
            "timestamp": "2025-05-23T12:34:56",
        }

    @app.tool(
        name="start_video_recording", description="Start recording video from a camera"
    )
    async def start_video_recording(
        device_id: str,
        resolution: Optional[str] = None,
        save_path: Optional[str] = None,
        duration: Optional[int] = None,
    ) -> Dict[str, Any]:
        return {
            "success": True,
            "recording_id": "rec123456",
            "file_path": save_path or "/tmp/mcp-peripherals/recording.mp4",
            "start_time": "2025-05-23T12:34:56",
            "resolution": resolution or "1920x1080",
            "max_duration": duration or "unlimited",
        }

    @app.tool(name="stop_video_recording", description="Stop recording video")
    async def stop_video_recording(recording_id: str) -> Dict[str, Any]:
        return {
            "success": True,
            "recording_id": recording_id,
            "file_path": "/tmp/mcp-peripherals/recording.mp4",
            "duration": "00:02:34",
            "file_size": "12.4 MB",
        }
