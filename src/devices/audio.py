from fastmcp import FastMCP
import pyaudio
import wave
from typing import Dict, List, Optional
from pydantic import Field
from typing import Annotated
import tempfile
import datetime
import os


def register_tools(app: FastMCP) -> None:
    @app.tool(
        name="list_audio_devices",
        description="List all available audio input and output devices",
        tags=["audio"],
    )
    async def list_audio_devices() -> Dict[str, List[Dict[str, any]]]:
        p = pyaudio.PyAudio()

        try:
            input_devices = []
            output_devices = []

            for i in range(p.get_device_count()):
                device_info = p.get_device_info_by_index(i)
                device_data = {
                    "index": i,
                    "name": device_info["name"],
                    "max_input_channels": device_info["maxInputChannels"],
                    "max_output_channels": device_info["maxOutputChannels"],
                    "default_sample_rate": device_info["defaultSampleRate"],
                    "host_api": p.get_host_api_info_by_index(device_info["hostApi"])[
                        "name"
                    ],
                }

                if device_info["maxInputChannels"] > 0:
                    input_devices.append(device_data)

                if device_info["maxOutputChannels"] > 0:
                    output_devices.append(device_data)

            return {"input_devices": input_devices, "output_devices": output_devices}
        finally:
            p.terminate()

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

        p = pyaudio.PyAudio()

        try:
            device_info = None
            if device_index is not None:
                device_info = p.get_device_info_by_index(device_index)
                if device_info["maxInputChannels"] == 0:
                    return {
                        "success": False,
                        "error": f"Device {device_index} is not an input device",
                    }

            stream = p.open(
                format=format,
                channels=channels,
                rate=sample_rate,
                input=True,
                frames_per_buffer=chunk,
                input_device_index=device_index,
            )

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

                p = pyaudio.PyAudio()

                try:
                    device_info = None
                    if device_index is not None:
                        device_info = p.get_device_info_by_index(device_index)
                        if device_info["maxOutputChannels"] == 0:
                            return {
                                "success": False,
                                "error": f"Device {device_index} is not an output device",
                            }

                    stream = p.open(
                        format=p.get_format_from_width(sample_width),
                        channels=channels,
                        rate=sample_rate,
                        output=True,
                        output_device_index=device_index,
                    )

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
            return {"success": False, "error": f"Audio file not found: {file_path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
