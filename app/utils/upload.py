# app/utils/upload.py
import os
import mimetypes
from botocore.exceptions import NoCredentialsError, ClientError
import boto3
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Define common MIME types for better control
MIME_TYPES = {
    # Images
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
    # Audio
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "ogg": "audio/ogg",
    # Video
    "mp4": "video/mp4",
    "webm": "video/webm",
    "avi": "video/x-msvideo",
    "mov": "video/quicktime",
}


def upload_to_do_spaces(
    file_path: str,
    object_name: str = None,
    file_type: str = None,
    content_type: str = None,
) -> str:
    """
    Upload a file to DigitalOcean Spaces with support for different file types.

    Args:
        file_path: Path to the file to upload
        object_name: S3 object name (if not specified, file_name is used)
        file_type: Type of file (e.g., 'image', 'audio', 'video') - determines folder
        content_type: MIME type, auto-detected if not specified

    Returns:
        The public URL of the uploaded file
    """
    try:
        # If object_name not specified, use the filename
        if object_name is None:
            object_name = os.path.basename(file_path)

        # Determine file type from extension if not specified
        if file_type is None:
            ext = os.path.splitext(file_path)[1].lower().lstrip(".")
            if ext in ["jpg", "jpeg", "png", "gif", "webp"]:
                file_type = "images"
            elif ext in ["mp3", "wav", "ogg"]:
                file_type = "audio"
            elif ext in ["mp4", "webm", "avi", "mov"]:
                file_type = "video"
            else:
                file_type = "files"  # default

        # Determine content type if not specified
        if content_type is None:
            ext = os.path.splitext(file_path)[1].lower().lstrip(".")
            content_type = MIME_TYPES.get(ext)

            # Fallback to mimetypes library if not in our mapping
            if content_type is None:
                content_type, _ = mimetypes.guess_type(file_path)

            # Final fallback
            if content_type is None:
                content_type = "application/octet-stream"

        # Ensure file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Create a session with DigitalOcean Spaces
        session = boto3.session.Session()
        s3_client = session.client(
            "s3",
            region_name=settings.DO_SPACES_REGION,
            endpoint_url=settings.DO_SPACES_ENDPOINT,
            aws_access_key_id=settings.DO_SPACES_KEY,
            aws_secret_access_key=settings.DO_SPACES_SECRET,
        )

        # Prepare object key (path in the bucket)
        object_key = f"{file_type}/{object_name}"

        logger.info(
            f"Uploading {file_path} to {object_key} with content type {content_type}"
        )

        # Upload the file
        s3_client.upload_file(
            file_path,
            settings.DO_SPACES_BUCKET,
            object_key,
            ExtraArgs={"ACL": "public-read", "ContentType": content_type},
        )

        # Generate the URL for the uploaded file
        url = f"{settings.DO_SPACES_BASE_URL}/{object_key}"
        logger.info(f"File uploaded to: {url}")
        return url

    except FileNotFoundError as e:
        logger.error(f"File not found: {file_path}")
        raise Exception(f"File not found: {file_path}")
    except (NoCredentialsError, ClientError) as e:
        logger.error(f"Error uploading to DO Spaces: {str(e)}")
        raise Exception(f"Failed to upload file: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}")
        raise Exception(f"Upload failed: {str(e)}")
