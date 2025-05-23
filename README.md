# MCP Device Server

A Model Context Protocol (MCP) server for seamless integration with peripheral devices connected to your computer. Control, monitor, and manage hardware devices through a unified API.

## Features

- **Multi-device Support**: Interact with cameras, printers, audio devices, storage devices, USB peripherals, and screens
- **Camera Control**: Capture images and record video from connected cameras
- **Print Management**: Send documents to printers and manage print jobs
- **Audio Capabilities**: Record from microphones and play audio through speakers
- **Storage Management**: Mount, unmount, and retrieve information about storage devices
- **Screen Capture**: Take screenshots and record screen activity from connected displays

## Usage

1. **Clone the repository**:

```bash
git clone https://github.com/akshitsinha/mcp-device-server.git
cd mcp-device-server
```

2. **Install required dependencies**:

```bash
uv sync
```

3. **Run the server**:

    **Option A: Run directly**:
    ```bash
    uv run src/main.py
    ```

    **Option B: Use with Claude Desktop**:
    
    Add the following configuration to your `claude_desktop_config.json`:
    ```json
    {
      "mcpServers": {
         "mcp-device-server": {
            "command": "uv",
            "args": ["--directory", "/path/to/mcp-device-server", "run", "src/main.py"]
         }
      }
    }
    ```
    
    Then restart Claude Desktop to load the server.

## Configuration

Configure the server using environment variables. You can set these or create a `.env` file in the project root.

**Available configuration options**:

```
MCP_HOST=127.0.0.1        # Server host address
MCP_PORT=8000             # Server port
MCP_ENABLE_CAMERA=true    # Enable camera functionality
MCP_ENABLE_PRINTER=true   # Enable printer functionality
MCP_ENABLE_AUDIO=true     # Enable audio functionality
MCP_ENABLE_STORAGE=true   # Enable storage functionality
MCP_ENABLE_SCREEN=true    # Enable screen functionality
```

## Available MCP Tools

### Camera

| Tool                    | Description                     |
| ----------------------- | ------------------------------- |
| `list_cameras`          | List all connected cameras      |
| `get_camera_info`       | Get detailed camera information |
| `capture_image`         | Take a picture from a camera    |
| `start_video_recording` | Begin video recording           |
| `stop_video_recording`  | End video recording             |

### Printer

| Tool                 | Description                |
| -------------------- | -------------------------- |
| `list_printers`      | List available printers    |
| `get_printer_status` | Get printer status details |
| `print_file`         | Send a file to a printer   |
| `get_print_job`      | Get print job information  |
| `cancel_print_job`   | Cancel a print job         |

### Audio

| Tool                   | Description                         |
| ---------------------- | ----------------------------------- |
| `list_audio_devices`   | List all audio input/output devices |
| `record_audio`         | Record from an input device         |
| `stop_audio_recording` | Stop audio recording                |
| `play_audio`           | Play audio through a device         |
| `stop_audio_playback`  | Stop audio playback                 |

### Device Management

| Tool              | Description                |
| ----------------- | -------------------------- |
| `list_devices`    | List all connected devices |
| `get_device_info` | Get device details         |

### Storage

| Tool                   | Description                    |
| ---------------------- | ------------------------------ |
| `list_storage_devices` | List connected storage devices |
| `get_storage_info`     | Get storage device details     |
| `mount_storage`        | Mount a storage device         |
| `unmount_storage`      | Unmount a storage device       |

### Screen

| Tool                    | Description             |
| ----------------------- | ----------------------- |
| `list_displays`         | List connected displays |
| `capture_screen`        | Take a screenshot       |
| `record_screen`         | Start screen recording  |
| `stop_screen_recording` | Stop screen recording   |

## License

[MIT License](LICENSE.md)
