import os
from src.utils.switchblade_decorator import tool

#geenralized function for upload the file on cloud storage

@tool(
    name="cloud_storage_sync",
    description="Generalized tool to move files from a local directory to a cloud destination. Supports future expansion for different cloud providers or protocols.",
    input_schema={
        "type": "object",
        "properties": {
            "local_path": {"type": "string", "description": "Local directory to upload."},
            "cloud_bucket": {"type": "string", "description": "Target cloud bucket name."},
            "cloud_path": {"type": "string", "description": "Destination folder in the cloud."},
            "provider": {"type": "string", "description": "The cloud provider (e.g., 'generic', 'aws', 'gcp')."}
        },
        "required": ["local_path", "cloud_bucket", "cloud_path"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "success, not_successful, or error"},
            "response": {"type": "string"},
            "detection_flag": {"type": "boolean"}
        },
    }
)
def cloud_storage_sync(args):
    local_dir = args.get("local_path")
    bucket = args.get("cloud_bucket")
    remote_dest = args.get("cloud_path")
    provider = args.get("provider", "generic").lower()
    
    upload_count = 0

    try:
        if not os.path.exists(local_dir):
            return {"status": "not_successful", "response": "Source path not found.", "detection_flag": False}

        # --- ROUTER LOGIC ---
        # This is where you can add new attributes for other attack trees in the future
        for root, _, files in os.walk(local_dir):
            for name in files:
                file_full_path = os.path.join(root, name)
                
                if provider == "generic":
                    # Put your current simple upload logic here
                    print(f"Uploading {name} to {bucket}/{remote_dest}")
                    upload_count += 1
                
                # FUTURE ATTRIBUTE EXAMPLE:
                # elif provider == "aws":
                #     s3.upload_file(file_full_path, bucket, remote_dest)

        if upload_count > 0:
            return {
                "status": "success",
                "response": f"Successfully moved {upload_count} files to {provider} storage.",
                "detection_flag": True
            }
        
        return {"status": "not_successful", "response": "No files found to move.", "detection_flag": False}

    except Exception as e:
        return {"status": "error", "response": f"Upload failed: {str(e)}", "detection_flag": False}