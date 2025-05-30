from typing import Dict, List, Optional, Any
from screeninfo import get_monitors
from fastmcp import FastMCP, Image
from PIL import Image as PILImage
from datetime import datetime
from typing import Annotated
from pydantic import Field
from mss import mss
import subprocess
import platform
import tempfile
import asyncio
import os
import io

_active_screen_recording = None


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
            str,
            Field(
                description="The display identifier in format 'displayN' where N is the display index (e.g., 'display0', 'display1')",
                default="display0",
            ),
        ] = "display0",
        save_path: Annotated[
            Optional[str],
            Field(
                description="The file path with filename where the screenshot should be saved. If None, a temporary file with timestamp will be created automatically"
            ),
        ] = None,
        return_image: Annotated[
            bool,
            Field(
                default=False,
                description="Whether to return the screenshot only, managing to stay within MCP response limits.",
            ),
        ] = False,
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
                system = platform.system()
                error_msg = "No displays found."
                if system == "Linux":
                    error_msg += " On Linux, ensure X11 or Wayland is running and display permissions are granted."
                elif system == "Windows":
                    error_msg += " Ensure display drivers are properly installed."
                elif system == "Darwin":
                    error_msg += " Check macOS display permissions in System Preferences > Security & Privacy > Privacy > Screen Recording."
                return {"success": False, "error": error_msg}

            if display_index >= len(monitors):
                return {
                    "success": False,
                    "error": f"Display {device_id} not found. Available displays: 0-{len(monitors) - 1}",
                }

            try:
                with mss() as sct:
                    if save_path is None:
                        temp_dir = tempfile.gettempdir()
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        save_path = os.path.join(
                            temp_dir, f"screenshot_{timestamp}.png"
                        )
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

                        dir_path = os.path.dirname(save_path)
                        if dir_path:
                            os.makedirs(dir_path, exist_ok=True)

                    sct.shot(mon=display_index + 1, output=save_path)

                    if not os.path.exists(save_path):
                        return {
                            "success": False,
                            "error": "Screenshot file was not created",
                        }

                    result = {
                        "success": True,
                        "file_path": save_path,
                        "file_size": os.path.getsize(save_path),
                    }

                    if return_image:
                        try:
                            with PILImage.open(save_path) as img:
                                max_size = 512
                                original_width, original_height = img.size

                                scale_factor = min(
                                    max_size / original_width,
                                    max_size / original_height,
                                )
                                new_width = int(original_width * scale_factor)
                                new_height = int(original_height * scale_factor)

                                img = img.resize(
                                    (new_width, new_height), PILImage.Resampling.LANCZOS
                                )

                                img_bytes = io.BytesIO()
                                img.save(img_bytes, format="PNG", optimize=True)
                                img_bytes.seek(0)

                                return Image(data=img_bytes.getvalue(), format="png")
                        except Exception as e:
                            result["image_error"] = f"Failed to create image: {str(e)}"

                    return result
            except PermissionError as e:
                system = platform.system()
                error_msg = f"Permission denied: {str(e)}."
                if system == "Darwin":
                    error_msg += " Grant screen recording permissions in System Preferences > Security & Privacy > Privacy > Screen Recording."
                elif system == "Linux":
                    error_msg += " Check X11/Wayland permissions or run with appropriate privileges."
                return {"success": False, "error": error_msg}
        except Exception as e:
            return {"success": False, "error": f"Screenshot capture failed: {str(e)}"}

    @app.tool(
        name="record_screen", description="Start recording a screen", tags=["screen"]
    )
    async def record_screen(
        device_id: Annotated[
            Optional[str],
            Field(
                description="The display identifier which should be passed as input format to ffmpeg.",
                default="0",
            ),
        ] = "0",
        save_path: Annotated[
            Optional[str],
            Field(
                description="The file path with or without file name where the video should be saved. If None, a temporary file with timestamp will be created automatically"
            ),
        ] = None,
        duration: Annotated[
            Optional[int],
            Field(
                description="Duration of the recording in seconds. If -1, records in background until stop_record_screen is called. If None, defaults to 3 seconds",
                default=3,
            ),
        ] = 3,
        fps: Annotated[
            Optional[float],
            Field(
                description="Frames per second for the recording. If None, defaults to 15 fps",
                default=15.0,
            ),
        ] = 15.0,
    ) -> Dict[str, Any]:
        global _active_screen_recording

        try:
            if _active_screen_recording is not None:
                return {
                    "success": False,
                    "error": "Another screen recording is already in progress. Stop it first using stop_record_screen.",
                }

            if duration is not None and duration != -1 and duration <= 0:
                return {
                    "success": False,
                    "error": "Duration must be positive or -1 for background recording",
                }
            if fps and fps <= 0:
                return {"success": False, "error": "FPS must be positive"}
            if fps and fps > 60:
                return {
                    "success": False,
                    "error": "FPS should not exceed 60 for optimal performance",
                }

            display_index = 0
            if device_id and device_id.startswith("display"):
                display_index = int(device_id.replace("display", ""))

            monitors = get_monitors()
            if not monitors:
                system = platform.system()
                error_msg = "No displays found."
                if system == "Linux":
                    error_msg += " On Linux, ensure X11 or Wayland is running and display permissions are granted."
                elif system == "Windows":
                    error_msg += " Ensure display drivers are properly installed."
                elif system == "Darwin":
                    error_msg += " Check macOS display permissions in System Preferences > Security & Privacy > Privacy > Screen Recording."
                return {"success": False, "error": error_msg}

            if display_index >= len(monitors) or display_index < 0:
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

                dir_path = os.path.dirname(save_path)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)

            try:
                result = subprocess.run(
                    ["ffmpeg", "-version"], capture_output=True, text=True, timeout=10
                )
                if result.returncode != 0:
                    raise FileNotFoundError("FFmpeg not found or not working")
            except (
                subprocess.TimeoutExpired,
                subprocess.CalledProcessError,
                FileNotFoundError,
            ):
                system = platform.system()
                install_commands = {
                    "Windows": "winget install ffmpeg  OR  download from https://ffmpeg.org/",
                    "Darwin": "brew install ffmpeg",
                    "Linux": "sudo apt install ffmpeg  OR  sudo yum install ffmpeg",
                }
                return {
                    "success": False,
                    "error": f"Screen recording requires FFmpeg. Install it using: {install_commands.get(system, 'ffmpeg')}",
                }

            system = platform.system()
            if system == "Windows":
                ffmpeg_args = [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "ddagrab",
                    "-framerate",
                    str(fps),
                    "-i",
                    f"\\\\.\\DISPLAY{display_index + 1}",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "ultrafast",
                    "-crf",
                    "23",
                    "-pix_fmt",
                    "yuv420p",
                    "-threads",
                    "2",
                ]
            elif system == "Darwin":
                ffmpeg_args = [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "avfoundation",
                    "-framerate",
                    str(fps),
                    "-pixel_format",
                    "bgr0",
                    "-i",
                    f"Capture screen {display_index}",
                    "-c:v",
                    "h264_videotoolbox",
                    "-preset",
                    "ultrafast",
                    "-crf",
                    "28",
                    "-pix_fmt",
                    "yuv420p",
                    "-threads",
                    "2",
                ]
            else:
                ffmpeg_args = [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "x11grab",
                    "-framerate",
                    str(fps),
                    "-i",
                    f":{display_index}",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "ultrafast",
                    "-crf",
                    "23",
                    "-pix_fmt",
                    "yuv420p",
                ]

            if duration != -1:
                ffmpeg_args.extend(["-t", str(duration)])

            ffmpeg_args.append(save_path)
            if duration == -1:
                proc = subprocess.Popen(
                    ffmpeg_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                _active_screen_recording = {
                    "process": proc,
                    "file_path": save_path,
                    "device_id": device_id,
                    "start_time": datetime.now(),
                }

                await asyncio.sleep(0.5)
                if proc.poll() is not None:
                    _active_screen_recording = None
                    try:
                        stdout, stderr = proc.communicate()
                        error_msg = stderr.decode() if stderr else "Unknown error"
                        return {
                            "success": False,
                            "error": f"Recording failed to start: {error_msg}",
                        }
                    except Exception as e:
                        return {
                            "success": False,
                            "error": "Recording failed to start: " + str(e),
                        }

                return {
                    "success": True,
                    "file_path": save_path,
                    "status": "recording_started",
                    "message": "Background recording started. Use stop_record_screen to stop.",
                }

            result = subprocess.run(ffmpeg_args, capture_output=True, text=True)
            if result.returncode != 0:
                error_details = result.stderr
                if "Permission denied" in error_details:
                    if system == "Darwin":
                        error_details += "\nGrant screen recording permissions in System Preferences > Security & Privacy > Privacy > Screen Recording."
                    elif system == "Linux":
                        error_details += "\nCheck X11/Wayland permissions or run with appropriate privileges."
                elif "No such file or directory" in error_details:
                    error_details += (
                        "\nEnsure FFmpeg is properly installed and accessible in PATH."
                    )
                elif "Invalid data found" in error_details:
                    error_details += "\nDisplay format may not be supported. Try a different display or check driver compatibility."

                return {
                    "success": False,
                    "error": f"FFmpeg recording failed: {error_details}",
                }

            if not os.path.exists(save_path) or os.path.getsize(save_path) == 0:
                return {
                    "success": False,
                    "error": "Video file was not created or is empty",
                }

            return {
                "success": True,
                "file_path": save_path,
            }
        except PermissionError as e:
            system = platform.system()
            error_msg = f"Permission denied: {str(e)}."
            if system == "Darwin":
                error_msg += " Grant screen recording permissions in System Preferences > Security & Privacy > Privacy > Screen Recording."
            elif system == "Linux":
                error_msg += (
                    " Check X11/Wayland permissions or run with appropriate privileges."
                )
            return {"success": False, "error": error_msg}
        except Exception as e:
            return {"success": False, "error": f"Screen recording failed: {str(e)}"}

    @app.tool(
        name="stop_record_screen",
        description="Stop the current background screen recording",
        tags=["screen"],
    )
    async def stop_record_screen() -> Dict[str, Any]:
        global _active_screen_recording

        if _active_screen_recording is None:
            return {"success": False, "error": "No active screen recording found"}

        try:
            process = _active_screen_recording["process"]
            file_path = _active_screen_recording["file_path"]
            device_id = _active_screen_recording["device_id"]
            start_time = _active_screen_recording["start_time"]

            process.terminate()

            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

            _active_screen_recording = None

            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                duration = (datetime.now() - start_time).total_seconds()
                return {
                    "success": True,
                    "file_path": file_path,
                    "device_id": device_id,
                    "duration": f"{duration:.1f} seconds",
                    "file_size": os.path.getsize(file_path),
                }
            else:
                return {
                    "success": False,
                    "error": "Recording was stopped but no valid file was created",
                }
        except Exception as e:
            _active_screen_recording = None
            return {
                "success": False,
                "error": f"Error stopping screen recording: {str(e)}",
            }
