import platform
import sys
import psutil
import subprocess
from datetime import datetime
from langchain.tools import tool

@tool
def get_os_info() -> str:
    """Get operating system details."""
    info = f"""
OS: {platform.system()} {platform.release()}
Version: {platform.version()}
Python: {sys.version.split()[0]}
Hostname: {platform.node()}
"""
    return info.strip()

@tool
def get_python_packages() -> str:
    """List installed Python packages using pip."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=columns"],
            capture_output=True,
            text=True,
            timeout=10
        )
        packages = result.stdout.split('\n')
        # Return first 15 packages
        return '\n'.join(packages[:17])
    except Exception as e:
        return f"Error listing packages: {str(e)}"

@tool
def check_process(process_name: str) -> str:
    """Check if a process is running. Args: process_name - name like 'python', 'chrome', 'node'."""
    found = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            if process_name.lower() in proc.info['name'].lower():
                found.append(f"PID: {proc.info['pid']} | Name: {proc.info['name']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if not found:
        return f"No processes found matching '{process_name}'"
    
    return f"Found {len(found)} process(es):\n" + "\n".join(found[:10])