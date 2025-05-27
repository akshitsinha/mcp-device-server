from typing import Dict, List, Optional, Any
from fastmcp import FastMCP
from screeninfo import get_monitors
from datetime import datetime
from mss import mss
import tempfile
import os
import time
from typing import Annotated
from pydantic import Field
from ffmpeg.asyncio import FFmpeg
import shutil


def register_tools(app: FastMCP) -> None:
    @app.tool(
        name="list_displays",
        description="List all displays connected to the system",
        tags=["screen"],
    )
    async def list_displays() -> List[Dict[str, Any]]:
        displays = []
        monitors = get_monitors()

        for i, monitor in enumerate(monitors):
            displays.append(
                {
                    "device_id": f"display{i}",
                    "name": f"Display {i}",
                    "resolution": f"{monitor.width}x{monitor.height}",
                    "is_primary": monitor.is_primary,
                    "x": monitor.x,
                    "y": monitor.y,
                }
            )

        return displays

    @app.tool(
        name="capture_screenshot",
        description="Capture a screenshot from a display",
        tags=["screen"],
    )
    async def capture_screenshot(
        device_id: Annotated[
            Optional[str],
            Field(
                description="The display identifier in format 'displayN' where N is the display index (e.g., 'display0', 'display1')",
                default="display0",
            ),
        ] = "display0",
        save_path: Annotated[
            Optional[str],
            Field(
                description="The file path with file name where the screenshot should be saved. If None, a temporary file with timestamp will be created automatically"
            ),
        ] = None,
    ) -> Dict[str, Any]:
        try:
            display_index = 0
            if device_id and device_id.startswith("display"):
                try:
                    display_index = int(device_id.replace("display", ""))
                except ValueError:
                    return {
                        "success": False,
                        "error": f"Invalid device_id format: {device_id}. Expected format: 'displayN'",
                    }

            monitors = get_monitors()
            if not monitors:
                return {"success": False, "error": "No displays found"}

            if display_index >= len(monitors):
                return {
                    "success": False,
                    "error": f"Display {device_id} not found. Available displays: 0-{len(monitors) - 1}",
                }

            with mss() as sct:
                if save_path is None:
                    temp_dir = tempfile.gettempdir()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_path = os.path.join(temp_dir, f"screenshot_{timestamp}.png")
                else:
                    if (
                        os.path.isdir(save_path)
                        or save_path.endswith("/")
                        or save_path.endswith("\\")
                    ):
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        save_path = os.path.join(
                            save_path, f"screenshot_{timestamp}.png"
                        )
                    else:
                        if not os.path.splitext(save_path)[1]:
                            save_path = save_path + ".png"

                    os.makedirs(os.path.dirname(save_path), exist_ok=True)

                sct.shot(mon=display_index + 1, output=save_path)
                return {
                    "success": True,
                    "file_path": save_path,
                }

        except Exception as e:
            return {"success": False, "error": f"Screenshot capture failed: {str(e)}"}

    @app.tool(
        name="record_screen", description="Start recording a screen", tags=["screen"]
    )
    async def record_screen(
        device_id: Annotated[
            Optional[str],
            Field(
                description="The display identifier in format 'displayN' where N is the display index (e.g., 'display0', 'display1')",
                default="display0",
            ),
        ] = "display0",
        save_path: Annotated[
            Optional[str],
            Field(
                description="The file path with or without file name where the video should be saved. If None, a temporary file with timestamp will be created automatically"
            ),
        ] = None,
        duration: Annotated[
            Optional[int],
            Field(
                description="Duration of the recording in seconds. If None, defaults to 10 seconds",
                default=10,
            ),
        ] = 10,
        fps: Annotated[
            Optional[float],
            Field(
                description="Frames per second for the recording. If None, defaults to 15 fps",
                default=15.0,
            ),
        ] = 15.0,
    ) -> Dict[str, Any]:
        try:
            display_index = 0
            if device_id and device_id.startswith("display"):
                try:
                    display_index = int(device_id.replace("display", ""))
                except ValueError:
                    return {
                        "success": False,
                        "error": f"Invalid device_id format: {device_id}. Expected format: 'displayN'",
                    }

            monitors = get_monitors()
            if not monitors:
                return {"success": False, "error": "No displays found"}

            if display_index >= len(monitors):
                return {
                    "success": False,
                    "error": f"Display {device_id} not found. Available displays: 0-{len(monitors) - 1}",
                }

            if save_path is None:
                temp_dir = tempfile.gettempdir()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = os.path.join(temp_dir, f"screen_recording_{timestamp}.mp4")
            else:
                if (
                    os.path.isdir(save_path)
                    or save_path.endswith("/")
                    or save_path.endswith("\\")
                ):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_path = os.path.join(
                        save_path, f"screen_recording_{timestamp}.mp4"
                    )
                else:
                    if not os.path.splitext(save_path)[1]:
                        save_path = save_path + ".mp4"

                os.makedirs(os.path.dirname(save_path), exist_ok=True)

            frames_dir = tempfile.mkdtemp()

            with mss() as sct:
                start_time = time.time()
                frame_count = 0

                while time.time() - start_time < duration:
                    sct.shot(
                        mon=display_index + 1,
                        output=f"{frames_dir}/frame_{frame_count:06d}.png",
                    )

                    frame_count += 1

            ffmpeg = (
                FFmpeg()
                .option("y")
                .input(f"{frames_dir}/frame_%06d.png", framerate=fps)
                .output(save_path, vcodec="libx264", pix_fmt="yuv420p")
            )

            await ffmpeg.execute()
            shutil.rmtree(frames_dir)
            return {"success": True, "file_path": save_path}

        except Exception as e:
            return {"success": False, "error": f"Screen recording failed: {str(e)}"}
