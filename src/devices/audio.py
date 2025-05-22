from typing import Dict, List, Optional, Any
from fastmcp import FastMCP


class AudioDevice:
    def __init__(self, device_id: str, name: str, is_input: bool):
        self.device_id = device_id
        self.name = name
        self.is_input = is_input


def register_tools(app: FastMCP) -> None:
    @app.tool(
        name="list_audio_devices",
        description="List all audio devices connected to the system",
    )
    async def list_audio_devices(
        input_only: bool = False, output_only: bool = False
    ) -> List[Dict[str, Any]]:
        devices = []

        if not output_only:
            devices.extend(
                [
                    {
                        "device_id": "mic0",
                        "name": "Built-in Microphone",
                        "type": "input",
                    },
                    {"device_id": "mic1", "name": "USB Microphone", "type": "input"},
                ]
            )

        if not input_only:
            devices.extend(
                [
                    {
                        "device_id": "spk0",
                        "name": "Built-in Speakers",
                        "type": "output",
                    },
                    {
                        "device_id": "spk1",
                        "name": "HDMI Audio Output",
                        "type": "output",
                    },
                ]
            )

        return devices

    @app.tool(name="record_audio", description="Record audio from an input device")
    async def record_audio(
        device_id: str,
        duration: Optional[int] = None,
        save_path: Optional[str] = None,
        format: str = "mp3",
        quality: str = "medium",
    ) -> Dict[str, Any]:
        return {
            "success": True,
            "recording_id": "audio123456",
            "device_id": device_id,
            "file_path": save_path or f"/tmp/mcp-peripherals/audio_recording.{format}",
            "start_time": "2025-05-23T12:34:56",
            "format": format,
            "quality": quality,
            "max_duration": duration or "unlimited",
        }

    @app.tool(name="stop_audio_recording", description="Stop recording audio")
    async def stop_audio_recording(recording_id: str) -> Dict[str, Any]:
        return {
            "success": True,
            "recording_id": recording_id,
            "file_path": "/tmp/mcp-peripherals/audio_recording.mp3",
            "duration": "00:02:34",
            "file_size": "3.2 MB",
        }

    @app.tool(name="play_audio", description="Play audio through an output device")
    async def play_audio(
        device_id: str, file_path: str, volume: Optional[int] = 100, loop: bool = False
    ) -> Dict[str, Any]:
        return {
            "success": True,
            "playback_id": "play123456",
            "device_id": device_id,
            "file_path": file_path,
            "duration": "00:03:45",
            "volume": volume,
            "loop": loop,
        }

    @app.tool(name="stop_audio_playback", description="Stop playing audio")
    async def stop_audio_playback(playback_id: str) -> Dict[str, Any]:
        return {"success": True, "playback_id": playback_id, "status": "stopped"}
