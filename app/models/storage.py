# app/models/storage.py

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class FileType(str, Enum):
    IMAGE = "images"
    AUDIO = "audio"
    VIDEO = "videos"
    DOCUMENT = "documents"
    OTHER = "files"


class FileUploadResponse(BaseModel):
    url: str = Field(..., description="Public URL of the uploaded file")
    key: str = Field(..., description="Object key in the storage")
    size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="Content type of the file")


class FileInfo(BaseModel):
    key: str = Field(..., description="Object key in the storage")
    size: int = Field(..., description="File size in bytes")
    last_modified: datetime = Field(..., description="Last modified timestamp")
    etag: str = Field(..., description="ETag of the object")
    content_type: Optional[str] = Field(None, description="Content type of the file")
    url: str = Field(..., description="Public URL of the file")
    is_directory: bool = Field(False, description="Whether this is a directory")


class ListFilesRequest(BaseModel):
    prefix: Optional[str] = Field(
        None, description="Directory prefix to list files from"
    )
    max_keys: Optional[int] = Field(
        1000, description="Maximum number of keys to return"
    )
    delimiter: Optional[str] = Field(
        "/", description="Delimiter for directory-like hierarchy"
    )


class ListFilesResponse(BaseModel):
    files: List[FileInfo] = Field([], description="List of files")
    directories: List[str] = Field([], description="List of directory prefixes")
    prefix: str = Field("", description="Current prefix/directory")
    is_truncated: bool = Field(False, description="Whether the results are truncated")
    next_marker: Optional[str] = Field(
        None, description="Marker for next set of results"
    )


class DeleteFileResponse(BaseModel):
    success: bool = Field(..., description="Whether the deletion was successful")
    key: str = Field(..., description="Key of the deleted object")


class DeleteMultipleFilesRequest(BaseModel):
    keys: List[str] = Field(..., description="List of object keys to delete")


class DeleteMultipleFilesResponse(BaseModel):
    success: bool = Field(..., description="Whether the operation was successful")
    deleted: List[str] = Field([], description="Keys that were successfully deleted")
    failed: Dict[str, str] = Field(
        {}, description="Keys that failed to delete and reasons"
    )


class CreateDirectoryRequest(BaseModel):
    path: str = Field(..., description="Directory path to create")


class CreateDirectoryResponse(BaseModel):
    success: bool = Field(..., description="Whether the directory was created")
    path: str = Field(..., description="Path of the created directory")


class CopyFileRequest(BaseModel):
    source_key: str = Field(..., description="Source object key")
    destination_key: str = Field(..., description="Destination object key")


class CopyFileResponse(BaseModel):
    success: bool = Field(..., description="Whether the file was copied")
    source: str = Field(..., description="Source key")
    destination: str = Field(..., description="Destination key")
    url: str = Field(..., description="Public URL of the new file")


class GetFileURLRequest(BaseModel):
    key: str = Field(..., description="Object key to get URL for")
    expiry: Optional[int] = Field(3600, description="URL expiry time in seconds")


class GetFileURLResponse(BaseModel):
    url: str = Field(..., description="URL to the file")
    expires_at: datetime = Field(..., description="When the URL expires")
