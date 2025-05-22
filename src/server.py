from fastmcp import FastMCP

from config import Settings
from devices import camera, printer, audio, storage, screen, usb


def create_app(settings: Settings) -> FastMCP:
    app = FastMCP(
        name="MCP Peripherals",
        settings=settings,
    )

    if settings.enable_camera:
        camera.register_tools(app)

    if settings.enable_printer:
        printer.register_tools(app)

    if settings.enable_audio:
        audio.register_tools(app)

    if settings.enable_storage:
        storage.register_tools(app)

    if settings.enable_screen:
        screen.register_tools(app)

    if settings.enable_usb:
        usb.register_tools(app)

    return app
