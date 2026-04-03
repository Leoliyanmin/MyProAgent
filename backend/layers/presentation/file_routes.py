from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from layers.presentation.dependencies import get_current_user_id
from layers.service.file_service import FileService

router = APIRouter(prefix="/files", tags=["Files"])
file_service = FileService()


class FileRenameRequest(BaseModel):
    files: List[dict]
    pattern: str


class FileConvertRequest(BaseModel):
    file_path: str
    target_format: str


@router.get("/list")
async def list_files(
    directory: str,
    pattern: Optional[str] = None,
    user_id: int = Depends(get_current_user_id)
):
    result = file_service.list_files(directory, pattern)
    return result


@router.post("/rename")
async def batch_rename(
    request: FileRenameRequest,
    user_id: int = Depends(get_current_user_id)
):
    result = file_service.batch_rename(request.files, request.pattern)
    return result


@router.post("/convert")
async def convert_format(
    request: FileConvertRequest,
    user_id: int = Depends(get_current_user_id)
):
    result = file_service.convert_format(request.file_path, request.target_format)
    return result
