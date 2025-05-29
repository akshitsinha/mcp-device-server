from typing import Dict, List, Optional
from typing import Annotated
from fastmcp import FastMCP
from pydantic import Field
import pyaudio
import wave
import tempfile
import datetime
import os
import platform


def register_tools(app: FastMCP) -> None:
    @app.tool(
        name="list_audio_devices",
        description="List all available audio input and output devices",
        tags=["audio"],
    )
    async def list_audio_devices() -> Dict[str, List[Dict[str, any]]]:
        try:
            p = pyaudio.PyAudio()
        except Exception as e:
            return {
                "input_devices": [],
                "output_devices": [],
                "error": f"Failed to initialize audio system: {str(e)}. "
                f"On {platform.system()}, ensure audio drivers are installed and permissions are granted.",
            }

        try:
            input_devices = []
            output_devices = []

            for i in range(p.get_device_count()):
                try:
                    device_info = p.get_device_info_by_index(i)
                    device_data = {
                        "name": device_info["name"],
                        "max_input_channels": device_info["maxInputChannels"],
                        "max_output_channels": device_info["maxOutputChannels"],
                        "default_sample_rate": device_info["defaultSampleRate"],
                        "host_api": p.get_host_api_info_by_index(
                            device_info["hostApi"]
                        )["name"],
                    }

                    if device_info["maxInputChannels"] > 0:
                        input_devices.append(device_data)

                    if device_info["maxOutputChannels"] > 0:
                        output_devices.append(device_data)
                except Exception:
                    continue

            return {"input_devices": input_devices, "output_devices": output_devices}
        except Exception as e:
            return {
                "input_devices": [],
                "output_devices": [],
                "error": f"Error listing devices: {str(e)}",
            }
        finally:
            try:
                p.terminate()
            except Exception:
                pass

    @app.tool(
        name="record_audio",
        description="Record audio from the microphone and save to a file",
        tags=["audio"],
    )
    async def record_audio(
        duration: Annotated[
            float, Field(default=5.0, description="Recording duration in seconds")
        ],
        sample_rate: Annotated[
            Optional[int], Field(default=44100, description="Sample rate in Hz")
        ] = 44100,
        channels: Annotated[
            Optional[int], Field(default=1, description="Number of audio channels")
        ] = 1,
        output_file: Annotated[
            Optional[str], Field(description="Output file path for the recorded audio")
        ] = None,
        device_index: Annotated[
            Optional[int],
            Field(
                default=None, description="Audio input device index (None for default)"
            ),
        ] = None,
    ) -> Dict[str, any]:
        chunk = 1024
        format = pyaudio.paInt16

        if output_file is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.wav"
            output_file = os.path.join(tempfile.gettempdir(), filename)

        try:
            p = pyaudio.PyAudio()
        except Exception as e:
            error_msg = f"Failed to initialize audio system: {str(e)}"
            if platform.system() == "Darwin":
                error_msg += " On macOS, check microphone permissions in System Preferences > Security & Privacy > Privacy > Microphone"
            elif platform.system() == "Linux":
                error_msg += " On Linux, ensure ALSA or PulseAudio is running and user has audio group permissions"
            elif platform.system() == "Windows":
                error_msg += " On Windows, ensure audio drivers are installed and microphone is not in use by another application"
            return {"success": False, "error": error_msg}

        try:
            device_info = None
            if device_index is not None:
                device_info = p.get_device_info_by_index(device_index)
                if device_info["maxInputChannels"] == 0:
                    return {
                        "success": False,
                        "error": f"Device {device_index} is not an input device",
                    }
            else:
                device_index = p.get_default_input_device_info()["index"]
                device_info = p.get_default_input_device_info()

            try:
                stream = p.open(
                    format=format,
                    channels=channels,
                    rate=sample_rate,
                    input=True,
                    frames_per_buffer=chunk,
                    input_device_index=device_index,
                )
            except Exception as e:
                error_msg = f"Failed to open audio stream: {str(e)}"
                if "Invalid device" in str(e):
                    error_msg += f" Device index {device_index} may not exist or may not support the requested format."
                elif "Device unavailable" in str(e) or "busy" in str(e).lower():
                    error_msg += (
                        " Audio device is currently in use by another application."
                    )
                elif platform.system() == "Linux" and "ALSA" in str(e):
                    error_msg += " ALSA error - try different sample rate or check audio system configuration."
                return {"success": False, "error": error_msg}

            frames = []
            total_frames = int(sample_rate / chunk * duration)

            for i in range(total_frames):
                data = stream.read(chunk)
                frames.append(data)

            stream.stop_stream()
            stream.close()

            with wave.open(output_file, "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(p.get_sample_size(format))
                wf.setframerate(sample_rate)
                wf.writeframes(b"".join(frames))

            return {
                "success": True,
                "output_file": output_file,
                "duration": duration,
                "sample_rate": sample_rate,
                "channels": channels,
                "device_used": device_info["name"] if device_info else "Default device",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            p.terminate()

    @app.tool(
        name="play_audio",
        description="Play an audio file through the specified output device",
        tags=["audio"],
    )
    async def play_audio(
        file_path: Annotated[str, Field(description="Path to the audio file to play")],
        device_index: Annotated[
            Optional[int],
            Field(
                default=None, description="Audio output device index (None for default)"
            ),
        ] = None,
    ) -> Dict[str, any]:
        try:
            with wave.open(file_path, "rb") as wf:
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                sample_rate = wf.getframerate()
                frames = wf.getnframes()
                duration = frames / sample_rate

                try:
                    p = pyaudio.PyAudio()
                except Exception as e:
                    error_msg = f"Failed to initialize audio system: {str(e)}"
                    if platform.system() == "Darwin":
                        error_msg += " On macOS, check audio output permissions and ensure no other app is using exclusive access"
                    elif platform.system() == "Linux":
                        error_msg += " On Linux, ensure ALSA or PulseAudio is running"
                    elif platform.system() == "Windows":
                        error_msg += " On Windows, ensure audio drivers are installed"
                    return {"success": False, "error": error_msg}

                try:
                    device_info = None
                    if device_index is not None:
                        device_info = p.get_device_info_by_index(device_index)
                        if device_info["maxOutputChannels"] == 0:
                            return {
                                "success": False,
                                "error": f"Device {device_index} is not an output device",
                            }
                    else:
                        device_index = p.get_default_output_device_info()["index"]
                        device_info = p.get_default_output_device_info()

                    try:
                        stream = p.open(
                            format=p.get_format_from_width(sample_width),
                            channels=channels,
                            rate=sample_rate,
                            output=True,
                            output_device_index=device_index,
                        )
                    except Exception as e:
                        error_msg = f"Failed to open audio output stream: {str(e)}"
                        if "Invalid device" in str(e):
                            error_msg += f" Device index {device_index} may not exist or may not support playback."
                        elif "Device unavailable" in str(e) or "busy" in str(e).lower():
                            error_msg += " Audio device is currently in use by another application."
                        elif platform.system() == "Linux" and "ALSA" in str(e):
                            error_msg += " ALSA error - try different sample rate or check audio system configuration."
                        return {"success": False, "error": error_msg}

                    chunk = 1024
                    data = wf.readframes(chunk)

                    while data:
                        stream.write(data)
                        data = wf.readframes(chunk)

                    stream.stop_stream()
                    stream.close()

                    return {
                        "success": True,
                        "file_played": file_path,
                        "duration": duration,
                        "sample_rate": sample_rate,
                        "channels": channels,
                        "device_used": device_info["name"]
                        if device_info
                        else "Default device",
                    }
                finally:
                    p.terminate()
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"Audio file not found: {file_path}. Check the file path and ensure it exists.",
            }
        except wave.Error as e:
            return {
                "success": False,
                "error": f"Invalid WAV file format: {str(e)}. Ensure the file is a valid WAV audio file.",
            }
        except PermissionError:
            return {
                "success": False,
                "error": f"Permission denied accessing file: {file_path}. Check file permissions.",
            }
        except Exception as e:
            error_msg = f"Playback failed: {str(e)}"
            if platform.system() == "Windows" and "DirectSound" in str(e):
                error_msg += " Try updating your audio drivers or using a different audio device."
            elif platform.system() == "Darwin" and "CoreAudio" in str(e):
                error_msg += " Check macOS audio settings and ensure the device is not in exclusive mode."
            return {"success": False, "error": error_msg}
