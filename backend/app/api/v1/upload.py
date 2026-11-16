"""图片上传接口。"""

from fastapi import APIRouter, File, UploadFile

from app.core.deps import OwnerDep
from app.services.image import save_image

router = APIRouter(tags=["upload"])


@router.post("/upload", status_code=201)
async def upload_image(owner: OwnerDep, file: UploadFile = File(...)) -> dict:
    data = await file.read()
    return save_image(data, file.content_type)
