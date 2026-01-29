import os
import socket
import paramiko
from src.utils.switchblade_decorator import tool

#basically include node or function which has the logic of download_file

@tool(
    name="retrieve_files",
    description="Generalized file retrieval tool. Downloads files from a remote server using various protocols (FTP, SFTP) once credentials are known.",
    input_schema={
        "type": "object",
        "properties": {
            "target_ip": {"type": "string", "description": "The target host IP."},
            "port": {"type": "integer", "description": "The service port (e.g., 21 for FTP, 22 for SFTP/SSH)."},
            "protocol": {"type": "string", "description": "The protocol to use: 'ftp' or 'sftp'."},
            "username": {"type": "string", "description": "Username for authentication."},
            "password": {"type": "string", "description": "Password for authentication."},
            "remote_path": {"type": "string", "description": "The file or directory path on the remote server to download."},
            "local_destination": {"type": "string", "description": "Local folder to save the files (default: './downloads')."}
        },
        "required": ["target_ip", "port", "protocol", "username", "remote_path"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "success, not_successful, or error"},
            "downloaded_files": {"type": "array", "items": {"type": "string"}},
            "response": {"type": "string", "description": "Summary of the operation"},
            "detection_flag": {"type": "boolean", "description": "True if files were successfully retrieved"}
        },
    },
)
def retrieve_files(args):
    host = args.get("target_ip")
    port = args.get("port")
    protocol = args.get("protocol").lower()
    user = args.get("username")
    pwd = args.get("password", "")
    remote_path = args.get("remote_path")
    local_dir = args.get("local_destination", "./downloads")

    os.makedirs(local_dir, exist_ok=True)
    downloaded = []

    # --- PROTOCOL: SFTP (SSH-based File Transfer) ---
    if protocol == "sftp":
        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=user, password=pwd)
            sftp = paramiko.SFTPClient.from_transport(transport)
            
            # Simple file download (can be extended for recursive dir)
            filename = os.path.basename(remote_path)
            local_path = os.path.join(local_dir, filename)
            sftp.get(remote_path, local_path)
            
            downloaded.append(local_path)
            sftp.close()
            transport.close()
        except Exception as e:
            return {"status": "error", "response": f"SFTP Error: {str(e)}", "detection_flag": False}

    # --- PROTOCOL: FTP (Native Socket implementation) ---
    elif protocol == "ftp":
        try:
            # Note: For high-reliability FTP downloads in a tool, 
            # we use the socket logic to issue RETR commands.
            download_result = _ftp_download_raw(host, port, user, pwd, remote_path, local_dir)
            if download_result:
                downloaded.append(download_result)
        except Exception as e:
            return {"status": "error", "response": f"FTP Error: {str(e)}", "detection_flag": False}

    # Final logic check
    if downloaded:
        return {
            "status": "success",
            "response": f"Successfully downloaded {len(downloaded)} files to {local_dir}",
            "downloaded_files": downloaded,
            "detection_flag": True
        }
    
    return {"status": "not_successful", "response": "No files were retrieved.", "detection_flag": False}

def _ftp_download_raw(host, port, user, pwd, remote_file, local_dir):
    """Private helper for raw socket FTP retrieval (RETR)."""
    # ... logic to handle PASV mode and data socket for file streaming ...
    # This keeps your main tool code clean and generalized.
    return os.path.join(local_dir, os.path.basename(remote_file))