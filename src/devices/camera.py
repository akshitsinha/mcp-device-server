from typing import Dict, List, Any, Optional
from datetime import datetime
from typing import Annotated
from fastmcp import FastMCP
from pydantic import Field
import cv2
import os
import tempfile
import asyncio
import platform
import subprocess

_active_video_recording = None


def register_tools(app: FastMCP) -> None:
    @app.tool(
        name="list_cameras",
        description="List all cameras connected to the system",
        tags=["camera"],
    )
    async def list_cameras() -> List[Dict[str, str]]:
        cameras = []
        found_cameras = set()

        for i in range(10):
            if i in found_cameras:
                continue

            cap = None
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        cameras.append(
                            {
                                "device_id": f"cam{i}",
                                "name": f"Camera {i}",
                                "backend": cap.getBackendName(),
                            }
                        )
                        found_cameras.add(i)
                        cap.release()
                        continue
                cap.release()

                backends = [cv2.CAP_ANY]
                system = platform.system().lower()

                if system == "windows":
                    backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF] + backends
                elif system == "darwin":
                    backends = [cv2.CAP_AVFOUNDATION] + backends
                elif system == "linux":
                    backends = [cv2.CAP_V4L2, cv2.CAP_GSTREAMER] + backends

                for backend in backends:
                    try:
                        cap = cv2.VideoCapture(i, backend)
                        if cap.isOpened():
                            ret, frame = cap.read()
                            if ret and frame is not None:
                                cameras.append(
                                    {
                                        "device_id": f"cam{i}",
                                        "name": f"Camera {i}",
                                        "backend": cap.getBackendName(),
                                    }
                                )
                                found_cameras.add(i)
                                cap.release()
                                break
                        cap.release()
                    except Exception:
                        if cap:
                            cap.release()
                        continue
            except Exception:
                if cap:
                    cap.release()
                continue

        return cameras

    @app.tool(
        name="get_camera_info",
        description="Get detailed information about a camera",
        tags=["camera"],
    )
    async def get_camera_info(
        device_id: Annotated[
            str,
            Field(
                default="cam0",
                description="The ID of the camera to retrieve information for",
            ),
        ] = "cam0",
    ) -> Dict[str, Any]:
        cap = None
        try:
            if device_id.startswith("cam"):
                cam_index = int(device_id[3:])
            else:
                return {
                    "error": "Invalid device_id format",
                    "platform": platform.system(),
                }

            system = platform.system().lower()
            backends = []
            if system == "windows":
                backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
            elif system == "linux":
                backends = [cv2.CAP_V4L2, cv2.CAP_GSTREAMER, cv2.CAP_ANY]
            elif system == "darwin":
                backends = [cv2.CAP_AVFOUNDATION, cv2.CAP_ANY]
            else:
                backends = [cv2.CAP_ANY]

            for backend in backends:
                try:
                    cap = cv2.VideoCapture(cam_index, backend)
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            break
                        cap.release()
                        cap = None
                except Exception:
                    if cap:
                        cap.release()
                        cap = None
                    continue

            if not cap or not cap.isOpened():
                return {
                    "device_id": device_id,
                    "status": "unavailable",
                    "error": "Camera not accessible",
                    "platform": platform.system(),
                }

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            backend = cap.getBackendName()
            info = {
                "device_id": device_id,
                "name": f"Camera {device_id[3:]}",
                "resolution": f"{width}x{height}",
                "fps": fps,
                "backend": backend,
                "status": "available",
                "platform": platform.system(),
            }

            return info
        except Exception as e:
            return {
                "device_id": device_id,
                "status": "error",
                "error": str(e),
                "platform": platform.system(),
            }
        finally:
            if cap is not None:
                cap.release()

    @app.tool(
        name="capture_image",
        description="Capture an image from a camera",
        tags=["camera"],
    )
    async def capture_image(
        device_id: Annotated[
            str,
            Field(
                default="cam0",
                description="The ID of the camera to capture an image from",
            ),
        ] = "cam0",
        timer: Annotated[
            int,
            Field(
                default=0,
                description="Optional timer in seconds to wait before capturing the image. If None, captures immediately.",
            ),
        ] = 0,
        save_path: Annotated[
            Optional[str],
            Field(
                default=None,
                description="The file path where the captured image should be saved. If None, a temporary file will be created automatically.",
            ),
        ] = None,
    ) -> Dict[str, Any]:
        cap = None
        try:
            if device_id.startswith("cam"):
                cam_index = int(device_id[3:])
            else:
                return {"error": "Invalid device_id format"}

            system = platform.system().lower()
            backends = []
            if system == "windows":
                backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
            elif system == "linux":
                backends = [cv2.CAP_V4L2, cv2.CAP_GSTREAMER, cv2.CAP_ANY]
            elif system == "darwin":
                backends = [cv2.CAP_AVFOUNDATION, cv2.CAP_ANY]
            else:
                backends = [cv2.CAP_ANY]

            for backend in backends:
                try:
                    cap = cv2.VideoCapture(cam_index, backend)
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            break
                        cap.release()
                        cap = None
                except Exception:
                    if cap:
                        cap.release()
                        cap = None
                    continue

            if not cap or not cap.isOpened():
                return {
                    "status": "error",
                    "device_id": device_id,
                    "error": "Camera not accessible",
                }

            for _ in range(5):
                cap.read()

            await asyncio.sleep(timer)
            ret, frame = cap.read()

            if not ret or frame is None:
                return {
                    "device_id": device_id,
                    "status": "error",
                    "error": "Failed to capture frame",
                }

            if save_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_dir = tempfile.gettempdir()
                save_path = os.path.join(temp_dir, f"camera_capture_{timestamp}.jpg")
            elif os.path.isdir(save_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = os.path.join(save_path, f"camera_capture_{timestamp}.jpg")

            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, 95]
            success = cv2.imwrite(save_path, frame, encode_params)
            if not success:
                return {
                    "status": "error",
                    "device_id": device_id,
                    "error": "Failed to save image",
                }

            return {
                "status": "success",
                "device_id": device_id,
                "file_path": save_path,
            }
        except Exception as e:
            return {"status": "error", "device_id": device_id, "error": str(e)}
        finally:
            if cap is not None:
                cap.release()

    @app.tool(
        name="start_video_recording",
        description="Start recording video from a camera",
        tags=["camera"],
    )
    async def start_video_recording(
        device_id: Annotated[
            str,
            Field(
                default="cam0",
                description="The ID of the camera to record video from",
            ),
        ] = "cam0",
        save_path: Annotated[
            Optional[str],
            Field(
                default=None,
                description="The file path where the video should be saved. If None, a temporary file will be created automatically.",
            ),
        ] = None,
        timer: Annotated[
            int,
            Field(
                default=0,
                description="Optional timer in seconds to wait before starting recording. If None, starts immediately.",
            ),
        ] = 0,
        fps: Annotated[
            float,
            Field(
                default=30.0,
                description="Frames per second for the video recording. Defaults to 30 fps. Note: macOS cameras typically support maximum 30 fps.",
            ),
        ] = 30.0,
        duration: Annotated[
            int,
            Field(
                default=5,
                description="Duration of the video recording in seconds. If -1, records in background until stop_video_recording is called.",
            ),
        ] = 5,
    ) -> Dict[str, Any]:
        global _active_video_recording

        try:
            if _active_video_recording is not None:
                return {
                    "status": "error",
                    "error": "Another video recording is already in progress. Stop it first using stop_video_recording.",
                }

            if device_id.startswith("cam"):
                cam_index = int(device_id[3:])
            else:
                return {"status": "error", "error": "Invalid device_id format"}

            if duration != -1 and duration <= 0:
                return {
                    "status": "error",
                    "error": "Duration must be positive or -1 for background recording",
                }

            if fps <= 0:
                return {"status": "error", "error": "FPS must be positive"}

            system = platform.system().lower()
            if system == "darwin" and fps > 30:
                return {
                    "status": "error",
                    "error": "FPS cannot exceed 30 for macOS cameras. Use fps=30 or lower.",
                }

            cap = None
            width, height = None, None
            backends = []
            if system == "windows":
                backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
            elif system == "linux":
                backends = [cv2.CAP_V4L2, cv2.CAP_GSTREAMER, cv2.CAP_ANY]
            elif system == "darwin":
                backends = [cv2.CAP_AVFOUNDATION, cv2.CAP_ANY]
            else:
                backends = [cv2.CAP_ANY]

            for backend in backends:
                try:
                    cap = cv2.VideoCapture(cam_index, backend)
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                            cap.release()
                            break
                        cap.release()
                        cap = None
                except Exception:
                    if cap:
                        cap.release()
                        cap = None
                    continue

            if width is None or height is None:
                return {
                    "status": "error",
                    "error": "Could not determine camera resolution",
                }

            if save_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_dir = tempfile.gettempdir()
                save_path = os.path.join(temp_dir, f"camera_recording_{timestamp}.mp4")
            elif os.path.isdir(save_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = os.path.join(save_path, f"camera_recording_{timestamp}.mp4")

            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            await asyncio.sleep(timer)

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

            ffmpeg_args = ["ffmpeg", "-y"]

            if system == "windows":
                ffmpeg_args.extend(
                    [
                        "-f",
                        "dshow",
                        "-framerate",
                        str(fps),
                        "-video_size",
                        f"{width}x{height}",
                        "-i",
                        f"video=@device_pv_{cam_index}",
                    ]
                )
            elif system == "linux":
                ffmpeg_args.extend(
                    [
                        "-f",
                        "v4l2",
                        "-framerate",
                        str(fps),
                        "-video_size",
                        f"{width}x{height}",
                        "-i",
                        f"/dev/video{cam_index}",
                    ]
                )
            elif system == "darwin":
                ffmpeg_args.extend(
                    [
                        "-f",
                        "avfoundation",
                        "-framerate",
                        str(fps),
                        "-video_size",
                        f"{width}x{height}",
                        "-pixel_format",
                        "uyvy422",
                        "-i",
                        str(cam_index),
                    ]
                )
            else:
                ffmpeg_args.extend(
                    [
                        "-framerate",
                        str(fps),
                        "-video_size",
                        f"{width}x{height}",
                        "-i",
                        str(cam_index),
                    ]
                )

            ffmpeg_args.extend(
                [
                    "-vcodec",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-crf",
                    "23",
                    "-preset",
                    "superfast" if duration == -1 else "fast",
                ]
            )

            if duration != -1:
                ffmpeg_args.extend(["-t", str(duration)])

            ffmpeg_args.append(save_path)

            if duration == -1:
                proc = subprocess.Popen(
                    ffmpeg_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                _active_video_recording = {
                    "process": proc,
                    "file_path": save_path,
                    "device_id": device_id,
                    "start_time": datetime.now(),
                }

                await asyncio.sleep(0.5)

                if proc.poll() is not None:
                    _active_video_recording = None
                    try:
                        stdout, stderr = proc.communicate()
                        error_msg = stderr.decode() if stderr else "Unknown error"

                        return {
                            "status": "error",
                            "error": f"Recording failed to start: {error_msg}",
                        }
                    except Exception as e:
                        return {
                            "status": "error",
                            "error": f"Recording failed to start: {str(e)}",
                        }

                return {
                    "status": "success",
                    "device_id": device_id,
                    "file_path": save_path,
                    "recording_status": "started",
                    "resolution": f"{width}x{height}",
                    "message": "Background recording started. Use stop_video_recording to stop.",
                }

            result = subprocess.run(ffmpeg_args, capture_output=True, text=True)

            if result.returncode != 0:
                error_msg = result.stderr
                return {
                    "status": "error",
                    "device_id": device_id,
                    "error": f"Recording failed: {error_msg}",
                }

            if not os.path.exists(save_path):
                return {
                    "status": "error",
                    "device_id": device_id,
                    "error": "Recording failed - output file not created",
                }
            return {
                "status": "success",
                "device_id": device_id,
                "file_path": save_path,
                "resolution": f"{width}x{height}",
            }
        except Exception as e:
            if save_path and os.path.exists(save_path):
                try:
                    os.remove(save_path)
                except Exception:
                    pass
            return {"status": "error", "device_id": device_id, "error": str(e)}

    @app.tool(
        name="stop_video_recording",
        description="Stop the current background video recording",
        tags=["camera"],
    )
    async def stop_video_recording() -> Dict[str, Any]:
        global _active_video_recording

        if _active_video_recording is None:
            return {"status": "error", "error": "No active video recording found"}

        try:
            process = _active_video_recording["process"]
            file_path = _active_video_recording["file_path"]
            device_id = _active_video_recording["device_id"]
            start_time = _active_video_recording["start_time"]

            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

            _active_video_recording = None

            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                duration = (datetime.now() - start_time).total_seconds()
                return {
                    "status": "success",
                    "device_id": device_id,
                    "file_path": file_path,
                    "duration": f"{duration:.1f} seconds",
                }
            else:
                return {
                    "status": "error",
                    "error": "Recording was stopped but no valid file was created",
                }
        except Exception as e:
            _active_video_recording = None
            return {
                "status": "error",
                "error": f"Error stopping video recording: {str(e)}",
            }
