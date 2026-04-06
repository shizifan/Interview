import os

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from app.core.config import settings

router = APIRouter(tags=["文件访问"])


@router.get("/{file_path:path}")
async def get_file(file_path: str):
    """访问上传的文件"""
    full_path = os.path.join(settings.UPLOAD_DIR, file_path)
    if not os.path.isfile(full_path):
        return {"code": 404, "message": "文件不存在", "data": None}
    return FileResponse(full_path)
