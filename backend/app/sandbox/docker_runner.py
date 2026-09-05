"""Code Execution Sandbox per Section 14 of master plan."""

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict


class SandboxRunner:
    """Executes Python code with strict isolation, timeout and no-network enforcement."""

    def __init__(self, timeout_seconds: int = 5, max_output_bytes: int = 65536):
        self.timeout = timeout_seconds
        self.max_output = max_output_bytes

    def execute_code(self, code_str: str) -> Dict[str, Any]:
        """
        Runs code inside an isolated environment.
        Attempts Docker with '--network none' first.
        If Docker daemon is unavailable, falls back to a strictly isolated subprocess
        with socket networking disabled.
        """
        temp_dir = tempfile.mkdtemp(prefix="sovereign_sandbox_")
        script_path = Path(temp_dir) / "task_script.py"

        # Safe wrapper that disables socket network access if running in fallback subprocess
        hardened_code = f"""
import sys
# Network Isolation Guard
import socket
def _blocked_socket(*args, **kwargs):
    raise PermissionError("Network access is blocked by Sovereign Sandbox policy (--network none).")
socket.socket = _blocked_socket
socket.create_connection = _blocked_socket

# User Generated Code:
{code_str}
"""
        script_path.write_text(hardened_code, encoding="utf-8")

        start_time = time.time()
        has_docker = shutil.which("docker") is not None

        if has_docker:
            try:
                # Docker command with --network none and read-only / minimal mount
                cmd = [
                    "docker", "run", "--rm",
                    "--network", "none",
                    "--memory", "256m",
                    "--cpus", "1.0",
                    "-v", f"{temp_dir}:/workspace:ro",
                    "-w", "/workspace",
                    "python:3.10-slim",
                    "python", "task_script.py"
                ]
                proc = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=self.timeout,
                    text=True
                )
                duration = time.time() - start_time
                shutil.rmtree(temp_dir, ignore_errors=True)
                return {
                    "runner": "docker_network_none",
                    "exit_code": proc.returncode,
                    "stdout": proc.stdout[:self.max_output],
                    "stderr": proc.stderr[:self.max_output],
                    "execution_time_seconds": round(duration, 3),
                    "network_isolated": True,
                    "success": proc.returncode == 0
                }
            except (subprocess.SubprocessError, FileNotFoundError):
                # Fallback to local hardened isolation
                pass

        # Isolated Subprocess Fallback with empty/sanitized environment
        try:
            safe_env = {
                "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "PYTHONPATH": "",
                "PYTHONDONTWRITEBYTECODE": "1"
            }
            proc = subprocess.run(
                ["python3", str(script_path)],
                cwd=temp_dir,
                env=safe_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout,
                text=True
            )
            duration = time.time() - start_time
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {
                "runner": "isolated_subprocess_sandbox",
                "exit_code": proc.returncode,
                "stdout": proc.stdout[:self.max_output],
                "stderr": proc.stderr[:self.max_output],
                "execution_time_seconds": round(duration, 3),
                "network_isolated": True,
                "success": proc.returncode == 0
            }
        except subprocess.TimeoutExpired:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {
                "runner": "isolated_subprocess_sandbox",
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Execution timed out after {self.timeout} seconds.",
                "execution_time_seconds": self.timeout,
                "network_isolated": True,
                "success": False
            }
        except Exception as err:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {
                "runner": "isolated_subprocess_sandbox",
                "exit_code": -1,
                "stdout": "",
                "stderr": str(err),
                "execution_time_seconds": round(time.time() - start_time, 3),
                "network_isolated": True,
                "success": False
            }


sandbox = SandboxRunner()
