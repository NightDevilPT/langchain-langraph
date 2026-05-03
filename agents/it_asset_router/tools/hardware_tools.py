import psutil
import platform
from langchain.tools import tool

@tool
def get_cpu_info() -> str:
    """Get real-time CPU information: model, cores, usage percentage."""
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count(logical=True)
    
    info = f"""
CPU: {platform.processor()}
Cores: {cpu_count} logical
Usage: {cpu_percent}%
Architecture: {platform.machine()}
"""
    return info.strip()

@tool
def get_memory_info() -> str:
    """Get real-time RAM and swap memory information."""
    memory = psutil.virtual_memory()
    
    info = f"""
RAM: {memory.used / (1024**3):.1f}GB / {memory.total / (1024**3):.1f}GB ({memory.percent}%)
Available: {memory.available / (1024**3):.1f}GB
"""
    return info.strip()

@tool
def get_disk_info() -> str:
    """Get disk usage for root partition."""
    disk = psutil.disk_usage('/')
    
    info = f"""
Disk: {disk.used / (1024**3):.1f}GB / {disk.total / (1024**3):.1f}GB ({disk.percent}%)
Free: {disk.free / (1024**3):.1f}GB
"""
    return info.strip()