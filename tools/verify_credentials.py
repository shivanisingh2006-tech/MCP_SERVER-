import os
import time
import socket
import paramiko
from src.utils.switchblade_decorator import tool
import logging

# This hides all the "Traceback" noise and internal Paramiko errors
logging.getLogger("paramiko").setLevel(logging.WARNING)

def load_credentials(file_path):
    path = str(file_path).strip()
    try:
        with open(path, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []


@tool(
    name="verify_credentials",
    description="Generalized authentication tool. Can check for anonymous access or attempt specific credential logins for various protocols.",
    input_schema={
        "type": "object",
        "properties": {
            "target_ip": {"type": "string", "description": "The target host IP or hostname."},
            "port": {"type": "integer", "description": "The service port (e.g., 21, 22)."},
            "protocol": {"type": "string", "description": "The protocol to test (ftp, ssh)."},
            "check_type": {"type": "string", "description": "The type of check: 'anonymous' or 'login'."}
        },
        "required": ["target_ip", "port", "protocol", "check_type"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "success, not_successful, or error"},
            "response": {"type": "string", "description": "Detailed result message"},
            "detection_flag": {"type": "boolean", "description": "True if access/login was successful"},
        },
    },
)

def verify_credentials(args):
    host = args.get("target_ip")
    port = args.get("port")
    protocol = (args.get("protocol") or "").lower()
    check_type = args.get("check_type", "login")
    
    # Define paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    user_name_path = os.path.join(BASE_DIR, "ssh_username.txt")
    user_pass_path = os.path.join(BASE_DIR, "ssh_password.txt")
    
    usernames = load_credentials(user_name_path)
    passwords = load_credentials(user_pass_path)

    if not host or not port or not protocol:
        return {
            "status": "error",
            "response": "Invalid input arguments.",
            "detection_flag": False
        }

    if not usernames or not passwords:
        return {
            "status": "error",
            "response": "Username or password file missing or empty.",
            "detection_flag": False
        }

    # --- PROTOCOL: SSH ---
    if protocol == "ssh":
        for username in usernames:
            for password in passwords:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                try:
                    client.connect(
                        host,
                        port=port,
                        username=username,
                        password=password,
                        timeout=5,
                        auth_timeout=5,
                        banner_timeout=5,
                        look_for_keys=False,
                        allow_agent=False
                    )
                    client.close()
                    return {
                        "status": "success",
                        "response": f"SSH login successful for {username}:{password}",
                        "detection_flag": True
                    }
                except paramiko.AuthenticationException:
                    print(f"[-] Failed: {username}:{password}")
                    client.close()
                    time.sleep(0.2)
                except Exception as e:
                    print(f"[!] Server error on {username}:{password}: {e}")
                    client.close()
                    time.sleep(0.2) 
        
        return {
            "status": "not_successful",
            "response": "All SSH credential attempts failed.",
            "detection_flag": False
        }

    # --- PROTOCOL: FTP ---
    elif protocol == "ftp":
        if check_type == "anonymous":
            try:
                with socket.create_connection((host, port), timeout=30) as sock:
                    sock.recv(1024) 
                    sock.sendall(b"USER anonymous\r\n")
                    sock.recv(1024)
                    sock.sendall(b"PASS anonymous@\r\n")
                    resp = sock.recv(1024).decode(errors="ignore")
                    if "230" in resp:
                        return {
                            "status": "success",
                            "response": f"FTP anonymous success on {host}:{port}",
                            "detection_flag": True
                        }
            except Exception:
                pass 

        for username in usernames:
            for password in passwords:
                try:
                    with socket.create_connection((host, port), timeout=30) as sock:
                        sock.recv(1024) 
                        sock.sendall(f"USER {username}\r\n".encode())
                        sock.recv(1024)
                        sock.sendall(f"PASS {password}\r\n".encode())
                        resp = sock.recv(1024).decode()
                        if "230" in resp:
                            return {
                                "status": "success",
                                "response": f"FTP success: {username}:{password}",
                                "detection_flag": True
                            }
                except Exception:
                    pass # Fixed empty except block

        return {
            "status": "not_successful",
            "response": "FTP login failed for all combinations in wordlist.",
            "detection_flag": False
        }

    # Final fallback for unsupported protocols
    return {
        "status": "error", 
        "response": f"Protocol {protocol} is not supported.", 
        "detection_flag": False
    }

# if __name__ == "__main__":
#     args = {
#         "target_ip": "127.0.0.1", 
#         "port": 2222,
#         "protocol": "ssh",
#         "check_type": "login"
#     }
#     result = verify_credentials(args)
#     print(result)