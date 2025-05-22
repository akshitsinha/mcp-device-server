from typing import Dict, List, Any
from fastmcp import FastMCP


class Printer:
    def __init__(self, device_id: str, name: str):
        self.device_id = device_id
        self.name = name


def register_tools(app: FastMCP) -> None:
    @app.tool(
        name="list_printers", description="List all printers available on the system"
    )
    async def list_printers() -> List[Dict[str, str]]:
        printers = [
            {"device_id": "printer0", "name": "HP LaserJet Pro"},
            {"device_id": "printer1", "name": "EPSON WorkForce"},
        ]
        return printers

    @app.tool(
        name="get_printer_status",
        description="Get detailed status information about a printer",
    )
    async def get_printer_status(device_id: str) -> Dict[str, Any]:
        return {
            "device_id": device_id,
            "name": f"Printer {device_id}",
            "state": "idle",
            "jobs_queued": 0,
            "ink_levels": {
                "black": "75%",
                "cyan": "80%",
                "magenta": "65%",
                "yellow": "90%",
            },
        }

    @app.tool(name="print_file", description="Print a file using a specified printer")
    async def print_file(
        device_id: str,
        file_path: str,
        copies: int = 1,
        double_sided: bool = False,
        color: bool = True,
    ) -> Dict[str, Any]:
        return {
            "success": True,
            "job_id": "job123456",
            "printer": device_id,
            "file": file_path,
            "copies": copies,
            "double_sided": double_sided,
            "color": color,
            "status": "printing",
            "pages": 5,
        }

    @app.tool(name="get_print_job", description="Get information about a print job")
    async def get_print_job(job_id: str) -> Dict[str, Any]:
        return {
            "job_id": job_id,
            "printer": "printer0",
            "status": "printing",
            "progress": "60%",
            "pages_printed": 3,
            "total_pages": 5,
        }

    @app.tool(name="cancel_print_job", description="Cancel a print job")
    async def cancel_print_job(job_id: str) -> Dict[str, Any]:
        return {"success": True, "job_id": job_id, "status": "cancelled"}
