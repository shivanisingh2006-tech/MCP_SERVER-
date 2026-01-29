import subprocess
import re
import socket  # used to verify whether the target is a valid IP address or not
from src.utils.switchblade_decorator import tool

NMAP_EXE = r"C:\Program Files (x86)\Nmap\nmap.exe"

@tool(
    name="nmap_scan",
    description="Generalized nmap scanner using system commands to check if a port is open.",
    input_schema={
        "type": "object",
        "properties": {
            "target_ip": {"type": "string", "description": "IPv4 address or hostname"},
            "port": {"type": "integer", "description": "Port number to check (e.g. 21, 22)"},
        },
        "required": ["target_ip", "port"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "success, not_successful, or error"},
            "port_status": {"type": "string", "description": "open, closed, or filtered"},
            "detection_flag": {"type": "boolean", "description": "True if port is open"},
        },
    },
)
def nmap_scan(args):
    host = args.get("target_ip")
    port = str(args.get("port"))
    
    # 1. Resolve Hostname (Built-in Logic)
    try:
        target_ip = socket.gethostbyname(host)
    except socket.gaierror:
        return {"status": "error", "port_status": "unknown", "detection_flag": False}

    # 2. Run Nmap via Subprocess (No library needed)
    try:
        # -Pn: Skip ping, -p: Specific port
        command = [NMAP_EXE, "-Pn", "-p", port, "-sT", target_ip]
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        output = result.stdout

        # 3. Parse Output (Core Logic)
        if f"{port}/tcp open" in output:
            port_status = "open"
            detection_flag = True
            status = "success"
        elif "filtered" in output:
            port_status = "filtered"
            detection_flag = False
            status = "not_successful"
        else:
            port_status = "closed"
            detection_flag = False
            status = "not_successful"

        print(f"Log: Native Scan on {target_ip}:{port} -> {port_status}")
        
        return {
            "status": status,
            "port_status": port_status,
            "detection_flag": detection_flag
        }

    except FileNotFoundError:
        return {"status": "error", "port_status": "nmap_not_installed", "detection_flag": False}
    except Exception as e:
        return {"status": "error", "port_status": str(e), "detection_flag": False}
    
# if __name__ == "__main__":
#     args = {
#         "target_ip": "127.0.0.1", 
#         "port": 2222,
#     }
#     result = nmap_scan(args)
#     print(result)