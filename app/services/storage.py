# app/services/storage.py

import os
import boto3
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from botocore.exceptions import ClientError

from app.utils.upload import upload_to_do_spaces
from app.utils.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class StorageService:
    """Service for interacting with Digital Ocean Spaces (S3-compatible storage)"""

    def __init__(self):
        self.region = settings.DO_SPACES_REGION
        self.endpoint = settings.DO_SPACES_ENDPOINT
        self.bucket = settings.DO_SPACES_BUCKET
        self.base_url = settings.DO_SPACES_BASE_URL
        self.s3_client = self._create_client()

    def _create_client(self):
        """Create an S3 client for Digital Ocean Spaces"""
        session = boto3.session.Session()
        return session.client(
            "s3",
            region_name=self.region,
            endpoint_url=self.endpoint,
            aws_access_key_id=settings.DO_SPACES_KEY,
            aws_secret_access_key=settings.DO_SPACES_SECRET,
        )

    def upload_file(
        self,
        file_path: str,
        object_name: str = None,
        file_type: str = None,
        content_type: str = None,
    ) -> Dict[str, Any]:
        """
        Upload a file to Digital Ocean Spaces using the existing utility

        Returns:
            Dict with file information
        """
        try:
            # Use the existing upload utility
            url = upload_to_do_spaces(
                file_path=file_path,
                object_name=object_name,
                file_type=file_type,
                content_type=content_type,
            )

            # Get the object key from the URL
            key = url.replace(f"{self.base_url}/", "")

            # Get file size
            file_size = os.path.getsize(file_path)

            return {
                "url": url,
                "key": key,
                "size": file_size,
                "content_type": content_type or "application/octet-stream",
            }
        except Exception as e:
            logger.error(f"File upload failed: {str(e)}")
            raise

    def list_files(
        self, prefix: str = None, max_keys: int = 1000, delimiter: str = "/"
    ) -> Dict[str, Any]:
        """
        List files in a directory (prefix) in the storage

        Args:
            prefix: Directory-like prefix to list objects from
            max_keys: Maximum number of keys to return
            delimiter: Delimiter for directory-like hierarchy

        Returns:
            Dict containing files, directories, and pagination info
        """
        try:
            # Normalize prefix
            if prefix and not prefix.endswith(delimiter) and prefix != "":
                prefix = f"{prefix}{delimiter}"

            # If prefix is None, set it to empty string
            prefix = prefix or ""

            # List objects with pagination
            params = {
                "Bucket": self.bucket,
                "MaxKeys": max_keys,
                "Delimiter": delimiter,
                "Prefix": prefix,
            }

            response = self.s3_client.list_objects_v2(**params)

            # Process the response
            files = []
            if "Contents" in response:
                for obj in response["Contents"]:
                    # Skip the directory marker object
                    if obj["Key"] == prefix:
                        continue

                    file_info = {
                        "key": obj["Key"],
                        "size": obj["Size"],
                        "last_modified": obj["LastModified"],
                        "etag": obj["ETag"].strip('"'),
                        "url": f"{self.base_url}/{obj['Key']}",
                        "is_directory": False,
                        "content_type": self._get_content_type(obj["Key"]),
                    }
                    files.append(file_info)

            # Get directories (common prefixes)
            directories = []
            if "CommonPrefixes" in response:
                for common_prefix in response["CommonPrefixes"]:
                    # Extract directory name from the prefix
                    dir_name = common_prefix["Prefix"]
                    directories.append(dir_name)

            result = {
                "files": files,
                "directories": directories,
                "prefix": prefix,
                "is_truncated": response.get("IsTruncated", False),
                "next_marker": response.get("NextContinuationToken"),
            }

            return result

        except ClientError as e:
            logger.error(f"Failed to list files: {str(e)}")
            raise

    def _get_content_type(self, key: str) -> str:
        """Get the content type based on file extension"""
        from app.utils.upload import MIME_TYPES
        import mimetypes

        ext = os.path.splitext(key)[1].lower().lstrip(".")

        # First check our predefined MIME types
        if ext in MIME_TYPES:
            return MIME_TYPES[ext]

        # Then try the mimetypes library
        content_type, _ = mimetypes.guess_type(key)

        # Fallback
        return content_type or "application/octet-stream"

    def get_file_info(self, key: str) -> Dict[str, Any]:
        """
        Get information about a specific file

        Args:
            key: The object key

        Returns:
            Dict with file information
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket, Key=key)

            file_info = {
                "key": key,
                "size": response["ContentLength"],
                "last_modified": response["LastModified"],
                "etag": response["ETag"].strip('"'),
                "content_type": response.get("ContentType", "application/octet-stream"),
                "url": f"{self.base_url}/{key}",
                "is_directory": key.endswith("/") and response["ContentLength"] == 0,
                "metadata": response.get("Metadata", {}),
            }

            return file_info
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                logger.warning(f"File not found: {key}")
                raise FileNotFoundError(f"File not found: {key}")
            logger.error(f"Error getting file info: {str(e)}")
            raise

    def delete_file(self, key: str) -> bool:
        """
        Delete a file from storage

        Args:
            key: The object key to delete

        Returns:
            True if successful
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"Deleted object: {key}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting file {key}: {str(e)}")
            raise

    def delete_multiple_files(
        self, keys: List[str]
    ) -> Tuple[List[str], Dict[str, str]]:
        """
        Delete multiple files from storage

        Args:
            keys: List of object keys to delete

        Returns:
            Tuple of (deleted_keys, failed_deletes)
        """
        # S3 requires a specific format for bulk deletes
        objects = [{"Key": key} for key in keys]

        try:
            response = self.s3_client.delete_objects(
                Bucket=self.bucket, Delete={"Objects": objects}
            )

            # Get successfully deleted objects
            deleted = [obj["Key"] for obj in response.get("Deleted", [])]

            # Get failed deletions
            failed = {}
            if "Errors" in response:
                for error in response["Errors"]:
                    failed[error["Key"]] = error["Message"]

            return deleted, failed

        except ClientError as e:
            logger.error(f"Error in bulk delete: {str(e)}")
            raise

    def create_directory(self, path: str) -> bool:
        """
        Create a "directory" in S3 (actually just an empty object with a trailing slash)

        Args:
            path: Directory path to create

        Returns:
            True if successful
        """
        try:
            # Ensure path ends with a slash
            if not path.endswith("/"):
                path += "/"

            # Create an empty object with the directory name
            self.s3_client.put_object(Bucket=self.bucket, Key=path, Body="")

            logger.info(f"Created directory: {path}")
            return True

        except ClientError as e:
            logger.error(f"Error creating directory {path}: {str(e)}")
            raise

    def copy_file(self, source_key: str, destination_key: str) -> Dict[str, Any]:
        """
        Copy a file within the same bucket

        Args:
            source_key: Source object key
            destination_key: Destination object key

        Returns:
            Dict with copy information
        """
        try:
            # Check if source exists
            self.get_file_info(source_key)

            # Perform the copy
            copy_source = {"Bucket": self.bucket, "Key": source_key}
            self.s3_client.copy_object(
                CopySource=copy_source, Bucket=self.bucket, Key=destination_key
            )

            # Generate URL for the new object
            url = f"{self.base_url}/{destination_key}"

            return {
                "success": True,
                "source": source_key,
                "destination": destination_key,
                "url": url,
            }

        except FileNotFoundError:
            logger.error(f"Source file not found: {source_key}")
            raise
        except ClientError as e:
            logger.error(
                f"Error copying file from {source_key} to {destination_key}: {str(e)}"
            )
            raise

    def generate_presigned_url(self, key: str, expiry: int = 3600) -> Dict[str, Any]:
        """
        Generate a presigned URL for temporary access

        Args:
            key: Object key
            expiry: Expiry time in seconds

        Returns:
            Dict with URL and expiry information
        """
        try:
            # Check if file exists
            self.get_file_info(key)

            # Generate presigned URL
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expiry,
            )

            expires_at = datetime.now() + timedelta(seconds=expiry)

            return {"url": url, "expires_at": expires_at}

        except FileNotFoundError:
            logger.error(f"File not found for presigned URL: {key}")
            raise
        except ClientError as e:
            logger.error(f"Error generating presigned URL for {key}: {str(e)}")
            raise
