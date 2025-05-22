# MCP Peripherals Server

A Model Context Protocol (MCP) server for controlling, monitoring, and managing peripheral devices connected to a computer.

## Features

- Discover and manage cameras, printers, audio devices, storage devices, USB devices, and screens
- Take pictures and record video from connected cameras
- Print documents using available printers
- Record audio from microphones and play audio through speakers
- Mount, unmount, and get information about storage devices
- Capture screenshots and record screen activity

## Requirements

- Python 3.10+
- FastMCP v2.4.0+

## Installation

1. Clone this repository:

```bash
git clone https://github.com/yourusername/mcp-device-server.git
cd mcp-device-server
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
```

3. Install dependencies:

```bash
pip install -e .
```

## Configuration

The server can be configured using environment variables or by creating an `.env` file in the root directory. Copy the `.env.example` file to `.env` and modify the settings as needed.

Available configuration options:

```
MCP_HOST=127.0.0.1
MCP_PORT=8000
MCP_DATA_DIR=./data
MCP_TEMP_DIR=/tmp/mcp-peripherals
MCP_ENABLE_CAMERA=true
MCP_ENABLE_PRINTER=true
MCP_ENABLE_AUDIO=true
MCP_ENABLE_STORAGE=true
MCP_ENABLE_SCREEN=true
```

## Usage

Start the server:

```bash
python -m src.main
```

The server will start on the configured host and port (default: 127.0.0.1:8000).

## API Documentation

Once the server is running, you can view the API documentation at:

```
http://localhost:8000/docs
```

## Tools

The server provides the following MCP tools:

### Camera Tools

- `list_cameras` - List all cameras connected to the system
- `get_camera_info` - Get detailed information about a camera
- `capture_image` - Capture an image from a camera
- `start_video_recording` - Start recording video from a camera
- `stop_video_recording` - Stop recording video

### Printer Tools

- `list_printers` - List all printers available on the system
- `get_printer_status` - Get detailed status information about a printer
- `print_file` - Print a file using a specified printer
- `get_print_job` - Get information about a print job
- `cancel_print_job` - Cancel a print job

### Audio Tools

- `list_audio_devices` - List all audio devices connected to the system
- `record_audio` - Record audio from an input device
- `stop_audio_recording` - Stop recording audio
- `play_audio` - Play audio through an output device
- `stop_audio_playback` - Stop playing audio

### Device Tools

- `list_devices` - List all devices connected to the system
- `get_device_info` - Get detailed information about a specific device

### Storage Tools

- `list_storage_devices` - List all storage devices connected to the system
- `get_storage_info` - Get detailed information about a storage device
- `mount_storage` - Mount a storage device
- `unmount_storage` - Unmount a storage device

### Screen Tools

- `list_displays` - List all displays connected to the system
- `capture_screen` - Capture a screenshot from a display
- `record_screen` - Start recording a screen
- `stop_screen_recording` - Stop recording a screen

## Development

### Project Structure

```
mcp-peripherals/
├── src/
│   ├── main.py                   # Main entry point for the server
│   ├── server.py                 # FastMCP server setup and configuration
│   ├── config.py                 # Configuration management
│   ├── exceptions.py             # Custom exceptions
│   │
│   ├── devices/
│       ├── base.py               # Base device interface
│       ├── camera.py             # Camera device management
│       ├── printer.py            # Printer device management
│       ├── audio.py              # Audio device management
│       ├── storage.py            # Storage/block device management
│       ├── usb.py                # USB device management
│       ├── screen.py             # Screen recording functionality
│       │
│       ├── tools/                # MCP tools implementations
│       ├── schemas/              # Pydantic schemas for device operations
│       └── utils/                # Utility functions
```

## License

[MIT License](LICENSE)
