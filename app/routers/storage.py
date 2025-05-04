# app/routers/storage.py

import os
import tempfile
import shutil
from typing import Optional
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    Path,
    HTTPException,
    BackgroundTasks,
)

from app.models.storage import (
    FileUploadResponse,
    FileInfo,
    ListFilesResponse,
    ListFilesRequest,
    DeleteFileResponse,
    DeleteMultipleFilesRequest,
    DeleteMultipleFilesResponse,
    CreateDirectoryRequest,
    CreateDirectoryResponse,
    CopyFileRequest,
    CopyFileResponse,
    GetFileURLRequest,
    GetFileURLResponse,
    FileType,
)
from app.services.storage import StorageService
from app.utils.logger import get_logger
import uuid

router = APIRouter()
logger = get_logger(__name__)
storage_service = StorageService()


def cleanup_temp_file(file_path: str):
    """Background task to cleanup a temporary file"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        logger.error(f"Error cleaning up temp file {file_path}: {e}")


@router.post("/upload", response_model=FileUploadResponse, status_code=201)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    file_type: Optional[FileType] = Form(None),
    custom_filename: Optional[str] = Form(None),
    folder: Optional[str] = Form(None),
):
    """
    Upload a file to storage.

    - You can specify the file_type to determine the folder structure
    - Custom filename will be used instead of the original filename if provided
    - You can also specify a folder within the file_type directory
    """
    try:
        # Create a temporary file
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            # Copy uploaded file to temp file
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name

        # Add cleanup as background task
        background_tasks.add_task(cleanup_temp_file, temp_path)

        # Determine final filename and path
        if custom_filename:
            filename = custom_filename
        else:
            # Use original filename but ensure uniqueness with UUID
            name_part, ext_part = os.path.splitext(file.filename)
            filename = f"{name_part}_{uuid.uuid4().hex[:8]}{ext_part}"

        # Include folder in object name if provided
        object_name = filename
        if folder:
            # Normalize folder path (remove leading/trailing slashes)
            folder = folder.strip("/")
            object_name = f"{folder}/{filename}"

        # Upload the file
        result = storage_service.upload_file(
            file_path=temp_path,
            object_name=object_name,
            file_type=file_type.value if file_type else None,
            content_type=file.content_type,
        )

        return FileUploadResponse(**result)

    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


@router.post("/list", response_model=ListFilesResponse)
async def list_files(request: ListFilesRequest):
    """
    List files and directories in storage with pagination.

    - Use prefix to navigate into folders (e.g., 'images/' or 'images/subfolder/')
    - Results include both files and directory prefixes
    """
    try:
        result = storage_service.list_files(
            prefix=request.prefix,
            max_keys=request.max_keys,
            delimiter=request.delimiter,
        )
        return ListFilesResponse(**result)

    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.get("/info/{key:path}", response_model=FileInfo)
async def get_file_info(key: str = Path(..., description="Object key")):
    """
    Get detailed information about a specific file.

    The key should be the full path of the file after the bucket name.
    """
    try:
        result = storage_service.get_file_info(key)
        return FileInfo(**result)

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {key}")

    except Exception as e:
        logger.error(f"Error getting file info: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get file info: {str(e)}"
        )


@router.delete("/delete/{key:path}", response_model=DeleteFileResponse)
async def delete_file(key: str = Path(..., description="Object key to delete")):
    """
    Delete a file from storage.

    The key should be the full path of the file after the bucket name.
    """
    try:
        success = storage_service.delete_file(key)
        return DeleteFileResponse(success=success, key=key)

    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


@router.post("/delete-multiple", response_model=DeleteMultipleFilesResponse)
async def delete_multiple_files(request: DeleteMultipleFilesRequest):
    """
    Delete multiple files in a single request.

    This is more efficient than making multiple delete requests.
    """
    try:
        deleted, failed = storage_service.delete_multiple_files(request.keys)
        return DeleteMultipleFilesResponse(
            success=len(failed) == 0, deleted=deleted, failed=failed
        )

    except Exception as e:
        logger.error(f"Error in bulk delete: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete files: {str(e)}")


@router.post("/create-directory", response_model=CreateDirectoryResponse)
async def create_directory(request: CreateDirectoryRequest):
    """
    Create a new directory in storage.

    Note: S3 doesn't have true directories, but we can emulate them with empty objects.
    """
    try:
        success = storage_service.create_directory(request.path)
        return CreateDirectoryResponse(success=success, path=request.path)

    except Exception as e:
        logger.error(f"Error creating directory: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create directory: {str(e)}"
        )


@router.post("/copy", response_model=CopyFileResponse)
async def copy_file(request: CopyFileRequest):
    """
    Copy a file within the storage.

    This operation is performed server-side without downloading and re-uploading.
    """
    try:
        result = storage_service.copy_file(
            source_key=request.source_key, destination_key=request.destination_key
        )
        return CopyFileResponse(**result)

    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Source file not found: {request.source_key}"
        )

    except Exception as e:
        logger.error(f"Error copying file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to copy file: {str(e)}")


@router.post("/get-url", response_model=GetFileURLResponse)
async def get_presigned_url(request: GetFileURLRequest):
    """
    Generate a pre-signed URL for temporary access to a private file.

    The URL will expire after the specified time (default: 1 hour).
    """
    try:
        result = storage_service.generate_presigned_url(
            key=request.key, expiry=request.expiry
        )
        return GetFileURLResponse(**result)

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {request.key}")

    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate URL: {str(e)}")
