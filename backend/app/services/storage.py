"""
S3 Storage service for audio files
Handles upload, download, and management of audio recordings
"""
import os
import uuid
import logging
from pathlib import Path
from typing import Optional, BinaryIO
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Configuration
S3_BUCKET = os.getenv("S3_BUCKET", "qari-app-audio")
S3_REGION = os.getenv("S3_REGION", "us-east-1")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
USE_LOCAL_STORAGE = os.getenv("USE_LOCAL_STORAGE", "true").lower() == "true"

# Local storage fallback
LOCAL_STORAGE_DIR = Path("uploads")
LOCAL_STORAGE_DIR.mkdir(exist_ok=True)


def get_s3_client():
    """Get boto3 S3 client."""
    try:
        import boto3
        return boto3.client(
            "s3",
            region_name=S3_REGION,
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
        )
    except ImportError:
        logger.warning("boto3 not installed, using local storage")
        return None
    except Exception as e:
        logger.error(f"Failed to create S3 client: {e}")
        return None


def generate_file_key(user_id: str, file_type: str = "recording") -> str:
    """Generate a unique S3 key for a file."""
    timestamp = datetime.utcnow().strftime("%Y/%m/%d")
    file_id = str(uuid.uuid4())
    return f"{file_type}/{user_id}/{timestamp}/{file_id}"


async def upload_audio(
    file_data: BinaryIO,
    user_id: str,
    filename: str,
    content_type: str = "audio/webm",
) -> dict:
    """
    Upload audio file to S3 or local storage.
    Returns dict with file URL and metadata.
    """
    file_key = generate_file_key(user_id, "recordings")
    extension = Path(filename).suffix or ".webm"
    full_key = f"{file_key}{extension}"
    
    if USE_LOCAL_STORAGE or not AWS_ACCESS_KEY:
        # Use local storage
        return await _upload_local(file_data, full_key, content_type)
    else:
        # Use S3
        return await _upload_s3(file_data, full_key, content_type)


async def _upload_local(
    file_data: BinaryIO,
    file_key: str,
    content_type: str,
) -> dict:
    """Upload to local filesystem."""
    # Create directory structure
    file_path = LOCAL_STORAGE_DIR / file_key
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write file
    content = file_data.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    logger.info(f"Saved file locally: {file_path}")
    
    return {
        "url": f"/api/v1/files/{file_key}",
        "key": file_key,
        "size": len(content),
        "storage": "local",
    }


async def _upload_s3(
    file_data: BinaryIO,
    file_key: str,
    content_type: str,
) -> dict:
    """Upload to S3."""
    s3_client = get_s3_client()
    if not s3_client:
        return await _upload_local(file_data, file_key, content_type)
    
    try:
        content = file_data.read()
        
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=file_key,
            Body=content,
            ContentType=content_type,
        )
        
        # Generate presigned URL
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": file_key},
            ExpiresIn=3600 * 24,  # 24 hours
        )
        
        logger.info(f"Uploaded to S3: {file_key}")
        
        return {
            "url": url,
            "key": file_key,
            "size": len(content),
            "storage": "s3",
            "bucket": S3_BUCKET,
        }
    except Exception as e:
        logger.error(f"S3 upload failed: {e}, falling back to local")
        file_data.seek(0)
        return await _upload_local(file_data, file_key, content_type)


async def get_audio_url(file_key: str) -> Optional[str]:
    """Get URL for an audio file."""
    if USE_LOCAL_STORAGE or not AWS_ACCESS_KEY:
        file_path = LOCAL_STORAGE_DIR / file_key
        if file_path.exists():
            return f"/api/v1/files/{file_key}"
        return None
    
    s3_client = get_s3_client()
    if not s3_client:
        return None
    
    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": file_key},
            ExpiresIn=3600,
        )
        return url
    except Exception as e:
        logger.error(f"Failed to get S3 URL: {e}")
        return None


async def delete_audio(file_key: str) -> bool:
    """Delete an audio file."""
    if USE_LOCAL_STORAGE or not AWS_ACCESS_KEY:
        file_path = LOCAL_STORAGE_DIR / file_key
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    s3_client = get_s3_client()
    if not s3_client:
        return False
    
    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=file_key)
        return True
    except Exception as e:
        logger.error(f"Failed to delete from S3: {e}")
        return False


async def list_user_recordings(user_id: str, limit: int = 50) -> list:
    """List all recordings for a user."""
    prefix = f"recordings/{user_id}/"
    
    if USE_LOCAL_STORAGE or not AWS_ACCESS_KEY:
        user_dir = LOCAL_STORAGE_DIR / "recordings" / user_id
        if not user_dir.exists():
            return []
        
        files = []
        for file_path in user_dir.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(LOCAL_STORAGE_DIR)
                files.append({
                    "key": str(rel_path),
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime),
                })
        return files[:limit]
    
    s3_client = get_s3_client()
    if not s3_client:
        return []
    
    try:
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=prefix,
            MaxKeys=limit,
        )
        
        files = []
        for obj in response.get("Contents", []):
            files.append({
                "key": obj["Key"],
                "size": obj["Size"],
                "modified": obj["LastModified"],
            })
        return files
    except Exception as e:
        logger.error(f"Failed to list S3 objects: {e}")
        return []


def get_storage_stats(user_id: str) -> dict:
    """Get storage usage statistics for a user."""
    recordings = list_user_recordings(user_id, limit=1000)
    
    total_size = sum(r.get("size", 0) for r in recordings)
    
    return {
        "total_files": len(recordings),
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
    }
