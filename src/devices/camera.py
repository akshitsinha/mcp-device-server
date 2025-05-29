from typing import Dict, List, Any, Optional
from fastmcp import FastMCP
from pydantic import Field
from typing import Annotated
from ffmpeg.asyncio import FFmpeg
import cv2
import os
import tempfile
from datetime import datetime
import asyncio
import shutil


def register_tools(app: FastMCP) -> None:
    @app.tool(
        name="list_cameras",
        description="List all cameras connected to the system",
        tags=["camera"],
    )
    async def list_cameras() -> List[Dict[str, str]]:
        cameras = []
        try:
            for i in range(10):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    name = f"Camera {i}"

                    cameras.append({"device_id": f"cam{i}", "name": name})
                    cap.release()
                else:
                    break

            if not cameras:
                return []
        except Exception:
            return []

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
        try:
            if device_id.startswith("cam"):
                cam_index = int(device_id[3:])
            else:
                return {"error": "Invalid device_id format"}

            cap = cv2.VideoCapture(cam_index)
            if not cap.isOpened():
                return {
                    "device_id": device_id,
                    "status": "unavailable",
                    "error": "Camera not accessible",
                }

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            backend = cap.getBackendName()
            cap.release()

            return {
                "device_id": device_id,
                "name": f"Camera {cam_index}",
                "resolution": f"{width}x{height}",
                "fps": fps,
                "backend": backend,
                "connection_type": "USB" if backend == "DirectShow" else "Unknown",
                "status": "available",
            }
        except Exception as e:
            return {"device_id": device_id, "status": "error", "error": str(e)}

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
                default=1,
                description="Optional timer in seconds to wait before capturing the image. If None, captures in 1 second.",
            ),
        ] = 1,
        save_path: Annotated[
            str,
            Field(
                default=None,
                description="The file path where the captured image should be saved. If None, a temporary file will be created automatically.",
            ),
        ] = None,
    ) -> Dict[str, Any]:
        try:
            if device_id.startswith("cam"):
                cam_index = int(device_id[3:])
            else:
                return {"error": "Invalid device_id format"}

            cap = cv2.VideoCapture(cam_index)
            if not cap.isOpened():
                return {
                    "status": "error",
                    "device_id": device_id,
                    "error": "Camera not accessible",
                }

            await asyncio.sleep(timer)
            ret, frame = cap.read()
            cap.release()

            if not ret:
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

            success = cv2.imwrite(save_path, frame)
            if not success:
                return {
                    "status": "error",
                    "device_id": device_id,
                    "error": "Failed to save image",
                }

            return {"status": "success", "device_id": device_id, "file_path": save_path}
        except Exception as e:
            return {"status": "error", "device_id": device_id, "error": str(e)}

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
                default=1,
                description="Optional timer in seconds to wait before starting recording.",
            ),
        ] = 1,
        fps: Annotated[
            float,
            Field(
                default=30.0,
                description="Frames per second for the video recording. Defaults to 30 fps.",
            ),
        ] = 30.0,
        duration: Annotated[
            int,
            Field(
                default=5,
                description="Duration of the video recording in seconds.",
            ),
        ] = 5,
    ) -> Dict[str, Any]:
        try:
            if device_id.startswith("cam"):
                cam_index = int(device_id[3:])
            else:
                return {"error": "Invalid device_id format"}

            cap = cv2.VideoCapture(cam_index)
            if not cap.isOpened():
                return {
                    "status": "error",
                    "device_id": device_id,
                    "error": "Camera not accessible",
                }

            if save_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_dir = tempfile.gettempdir()
                save_path = os.path.join(temp_dir, f"camera_recording_{timestamp}.mp4")
            elif os.path.isdir(save_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = os.path.join(save_path, f"camera_recording_{timestamp}.mp4")

            temp_frames_dir = tempfile.mkdtemp(prefix="camera_frames_")
            await asyncio.sleep(timer)

            frame_count = int(fps * duration)
            saved_frames = []

            for i in range(frame_count):
                ret, frame = cap.read()
                if not ret:
                    break

                frame_path = os.path.join(temp_frames_dir, f"frame_{i:06d}.jpg")
                cv2.imwrite(frame_path, frame)
                saved_frames.append(frame_path)

                await asyncio.sleep(1.0 / fps)

            cap.release()

            if not saved_frames:
                return {
                    "status": "error",
                    "device_id": device_id,
                    "error": "No frames captured",
                }

            frame_pattern = os.path.join(temp_frames_dir, "frame_%06d.jpg")
            ffmpeg = (
                FFmpeg()
                .option("y")
                .input(frame_pattern, framerate=fps)
                .output(save_path, vcodec="libx264", pix_fmt="yuv420p")
            )

            await ffmpeg.execute()
            return {
                "status": "success",
                "device_id": device_id,
                "file_path": save_path,
            }
        except Exception as e:
            return {"status": "error", "device_id": device_id, "error": str(e)}
        finally:
            shutil.rmtree(temp_frames_dir, ignore_errors=True)
