from typing import Dict, List, Any
from fastmcp import FastMCP
from typing import Annotated
from pydantic import Field
import subprocess
import re
import tempfile
import os


class Printer:
    def __init__(self, printer_name: str):
        self.printer_name = printer_name


def register_tools(app: FastMCP) -> None:
    @app.tool(
        description="List all printers available on the system",
        tags=["printer"],
    )
    async def list_printers() -> List[Dict[str, str]]:
        try:
            result = subprocess.run(
                ["lpstat", "-p"], capture_output=True, text=True, check=True
            )
            printer_lines = result.stdout.strip().split("\n")

            printers = []
            for line in printer_lines:
                if line.startswith("printer ") and "enabled" in line:
                    match = re.match(r"printer (\S+)", line)
                    if match:
                        printer_name = match.group(1)
                        printer = Printer(printer_name=printer_name)
                        printers.append({"printer_name": printer.name})
        except subprocess.CalledProcessError:
            printers = []
        return printers

    @app.tool(
        name="print_file",
        description="Print a file using a specified printer",
        tags=["printer"],
    )
    async def print_file(
        file_data: Annotated[
            bytes, Field(description="Binary data of the file to be printed")
        ],
        file_format: Annotated[
            str, Field(description="File format of the file to be printed")
        ],
        printer_name: Annotated[
            str, Field(description="Name of the printer to use")
        ] = None,
        copies: Annotated[
            int, Field(description="Number of copies to print", ge=1)
        ] = 1,
        double_sided: Annotated[bool, Field(description="Print double-sided")] = False,
        color: Annotated[bool, Field(description="Print in color")] = False,
    ) -> Dict[str, Any]:
        if printer_name is None:
            try:
                result = subprocess.run(
                    ["lpstat", "-d"], capture_output=True, text=True, check=True
                )
                match = re.search(r"system default destination: (\S+)", result.stdout)
                if match:
                    printer_name = match.group(1)
                else:
                    return {"success": False, "error": "No default printer found"}
            except subprocess.CalledProcessError:
                return {"success": False, "error": "Failed to retrieve default printer"}

        with tempfile.TemporaryFile(
            delete=False, suffix=f".{file_format}"
        ) as temp_file:
            temp_file.write(file_data)
            file_path = temp_file.name

            try:
                lp_command = ["lp", "-d", printer_name, "-n", str(copies)]
                if double_sided:
                    lp_command.append("-o")
                    lp_command.append("sides=two-sided-long-edge")
                if not color:
                    lp_command.append("-o")
                    lp_command.append("ColorModel=Gray")
                lp_command.append(file_path)

                result = subprocess.run(
                    lp_command, capture_output=True, text=True, check=True
                )
                job_id_match = re.search(r"request id is (\S+)", result.stdout)
                if job_id_match:
                    job_id = job_id_match.group(1)
                    return {"success": True, "job_id": job_id, "printer": printer_name}
                else:
                    return {
                        "success": False,
                        "error": "Failed to retrieve print job ID",
                    }
            except subprocess.CalledProcessError as e:
                return {"success": False, "error": f"Printing failed: {e.stderr}"}
            finally:
                temp_file.close()

    @app.tool(
        name="print_as_pdf",
        description="Print a file as PDF to a specified device location",
        tags=["printer"],
    )
    async def print_as_pdf(
        file_data: Annotated[
            bytes, Field(description="Binary data of the PDF file to be saved")
        ],
        file_format: Annotated[str, Field(description="File format (must be 'pdf')")],
        output_path: Annotated[
            str, Field(description="Full path where the PDF should be saved")
        ],
    ) -> Dict[str, Any]:
        if file_format.lower() != "pdf":
            return {"success": False, "error": "File format must be 'pdf'"}

        try:
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            with open(output_path, "wb") as pdf_file:
                pdf_file.write(file_data)

            return {
                "success": True,
                "output_path": output_path,
                "file_size": len(file_data),
            }

        except OSError as e:
            return {"success": False, "error": f"Failed to save PDF: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    @app.tool(
        name="get_print_job",
        description="Get information about a print job",
        tags=["printer"],
    )
    async def get_print_job(job_id: str) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                ["lpstat", "-W", "not-completed", "-o", job_id],
                capture_output=True,
                text=True,
                check=True,
            )
            if result.stdout.strip():
                job_info = result.stdout.strip()
                match = re.search(r"(\S+)\s+\S+\s+(\d+)\s+(\d+)", job_info)
                if match:
                    printer_name = match.group(1)
                    pages_printed = int(match.group(2))
                    total_pages = int(match.group(3))
                    return {
                        "job_id": job_id,
                        "printer": printer_name,
                        "status": "printing",
                        "progress": f"{(pages_printed / total_pages) * 100:.2f}%",
                        "pages_printed": pages_printed,
                        "total_pages": total_pages,
                    }
                else:
                    return {"success": False, "error": "Failed to parse job details"}
            else:
                return {"success": False, "error": "No such job found"}
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Failed to retrieve job info: {e.stderr}",
            }

    @app.tool(
        name="cancel_print_job", description="Cancel a print job", tags=["printer"]
    )
    async def cancel_print_job(job_id: str) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                ["cancel", job_id],
                capture_output=True,
                text=True,
                check=True,
            )
            if result.returncode == 0:
                return {"success": True, "job_id": job_id, "status": "cancelled"}
            else:
                return {"success": False, "error": "Failed to cancel the print job"}
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": f"Failed to cancel job: {e.stderr}"}
