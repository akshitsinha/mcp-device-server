from typing import Dict, List, Any
from fastmcp import FastMCP
from typing import Annotated
from pydantic import Field
from time import time
import platform
import subprocess
import tempfile
import re
import os


def register_tools(app: FastMCP) -> None:
    @app.tool(
        description="List all printers available on the system",
        tags=["printer"],
    )
    async def list_printers() -> List[Dict[str, str]]:
        printers = []
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["wmic", "printer", "get", "name", "/format:csv"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                lines = result.stdout.strip().split("\n")[1:]
                for line in lines:
                    if line.strip() and "," in line:
                        parts = line.split(",")
                        if len(parts) >= 2 and parts[1].strip():
                            printer_name = parts[1].strip()
                            printers.append({"printer_name": printer_name})
            else:
                # Unix/Linux/macOS: Try lpstat first, fallback to other methods
                try:
                    result = subprocess.run(
                        ["lpstat", "-p"], capture_output=True, text=True, check=True
                    )
                    printer_lines = result.stdout.strip().split("\n")

                    for line in printer_lines:
                        if line.startswith("printer ") and "enabled" in line:
                            match = re.match(r"printer (\S+)", line)
                            if match:
                                printer_name = match.group(1)
                                printers.append({"printer_name": printer_name})

                except subprocess.CalledProcessError:
                    # Fallback: try lpoptions (available on some Linux systems)
                    try:
                        result = subprocess.run(
                            ["lpoptions", "-d"],
                            capture_output=True,
                            text=True,
                            check=True,
                        )
                        # lpoptions output: "destination printer-name options"
                        if result.stdout.strip():
                            parts = result.stdout.strip().split()
                            if len(parts) >= 2:
                                printer_name = parts[1]
                                printers.append({"printer_name": printer_name})
                    except subprocess.CalledProcessError:
                        pass  # No printers found or CUPS not available
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
                if platform.system() == "Windows":
                    result = subprocess.run(
                        [
                            "wmic",
                            "printer",
                            "where",
                            "default=true",
                            "get",
                            "name",
                            "/format:csv",
                        ],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    lines = result.stdout.strip().split("\n")[1:]
                    for line in lines:
                        if line.strip() and "," in line:
                            parts = line.split(",")
                            if len(parts) >= 2 and parts[1].strip():
                                printer_name = parts[1].strip()
                                break
                    if not printer_name:
                        return {"success": False, "error": "No default printer found"}
                else:
                    # Unix/Linux/macOS: Try multiple methods to get default printer
                    try:
                        result = subprocess.run(
                            ["lpstat", "-d"], capture_output=True, text=True, check=True
                        )
                        match = re.search(
                            r"system default destination: (\S+)", result.stdout
                        )
                        if match:
                            printer_name = match.group(1)
                        else:
                            raise subprocess.CalledProcessError(1, "lpstat")
                    except subprocess.CalledProcessError:
                        # Fallback: try lpoptions to get default printer
                        try:
                            result = subprocess.run(
                                ["lpoptions", "-d"],
                                capture_output=True,
                                text=True,
                                check=True,
                            )
                            if result.stdout.strip():
                                parts = result.stdout.strip().split()
                                if len(parts) >= 2:
                                    printer_name = parts[1]
                                else:
                                    return {
                                        "success": False,
                                        "error": "No default printer found",
                                    }
                            else:
                                return {
                                    "success": False,
                                    "error": "No default printer found",
                                }
                        except subprocess.CalledProcessError:
                            return {
                                "success": False,
                                "error": "No default printer found",
                            }
            except subprocess.CalledProcessError:
                return {"success": False, "error": "Failed to retrieve default printer"}

        with tempfile.NamedTemporaryFile(
            delete=False, suffix=f".{file_format}"
        ) as temp_file:
            temp_file.write(file_data)
            temp_file.flush()
            file_path = temp_file.name

            try:
                if platform.system() == "Windows":
                    powershell_command = [
                        "powershell",
                        "-Command",
                        f'$job = Start-Process -FilePath "{file_path}" -Verb Print -PassThru -WindowStyle Hidden; Write-Host "job-id:$($job.Id)"',
                    ]

                    if printer_name:
                        powershell_command = [
                            "powershell",
                            "-Command",
                            f'$printer = Get-WmiObject -Class Win32_Printer | Where-Object {{$_.Name -eq "{printer_name}"}}; if ($printer) {{ $job = ([System.Diagnostics.Process]::Start([System.Diagnostics.ProcessStartInfo]@{{FileName="{file_path}"; Verb="Print"; UseShellExecute=$true; WindowStyle="Hidden"}})); Start-Sleep -Milliseconds 500; Write-Host "job-id:win-$($job.Id)" }} else {{ Write-Error "Printer not found" }}',
                        ]

                    result = subprocess.run(
                        powershell_command,
                        capture_output=True,
                        text=True,
                        check=True,
                    )

                    job_id_match = re.search(r"job-id:(\S+)", result.stdout)
                    if job_id_match:
                        job_id = job_id_match.group(1)
                        return {
                            "success": True,
                            "job_id": job_id,
                            "printer": printer_name or "default",
                        }
                    else:
                        return {
                            "success": False,
                            "error": "Failed to retrieve print job ID from Windows",
                        }
                else:
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
                        return {
                            "success": True,
                            "job_id": job_id,
                            "printer": printer_name,
                        }
                    else:
                        return {
                            "success": False,
                            "error": "Failed to retrieve print job ID",
                        }
            except subprocess.CalledProcessError as e:
                return {"success": False, "error": f"Printing failed: {e.stderr}"}
            except Exception as e:
                return {"success": False, "error": f"Unexpected error: {str(e)}"}
            finally:
                try:
                    os.unlink(file_path)
                except OSError:
                    pass

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
            if os.path.isdir(output_path):
                timestamp = int(time())
                filename = f"document_{timestamp}.pdf"
                full_output_path = os.path.join(output_path, filename)
            else:
                full_output_path = output_path
                output_dir = os.path.dirname(full_output_path)
                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir, exist_ok=True)

            with open(full_output_path, "wb") as pdf_file:
                pdf_file.write(file_data)

            return {"success": True, "output_path": full_output_path}
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
            if platform.system() == "Windows":
                result = subprocess.run(
                    [
                        "wmic",
                        "printjob",
                        "where",
                        f"JobId={job_id}",
                        "get",
                        "Name,Status,PagesPrinted,TotalPages",
                        "/format:csv",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                if result.stdout.strip():
                    lines = result.stdout.strip().split("\n")[1:]
                    if lines and lines[0].strip():
                        parts = lines[0].split(",")
                        if len(parts) >= 4:
                            try:
                                pages_printed = int(parts[2]) if parts[2].strip() else 0
                                total_pages = int(parts[3]) if parts[3].strip() else 1
                                progress = (
                                    (pages_printed / total_pages) * 100
                                    if total_pages > 0
                                    else 0
                                )
                                return {
                                    "job_id": job_id,
                                    "status": "printing",
                                    "progress": f"{progress:.2f}%",
                                    "pages_printed": pages_printed,
                                    "total_pages": total_pages,
                                }
                            except (ValueError, ZeroDivisionError):
                                return {"job_id": job_id, "status": "printing"}
                        else:
                            return {"job_id": job_id, "status": "printing"}
                return {"success": False, "error": "No such job found"}
            else:
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
                        return {
                            "success": False,
                            "error": "Failed to parse job details",
                        }
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
            if platform.system() == "Windows":
                result = subprocess.run(
                    [
                        "wmic",
                        "printjob",
                        "where",
                        f"JobId={job_id}",
                        "delete",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                if result.returncode == 0:
                    return {
                        "success": True,
                        "job_id": job_id,
                        "status": "cancelled",
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to cancel the print job",
                    }
            else:
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
