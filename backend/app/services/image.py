"""图片上传：MIME + 魔数双重校验，统一转 webp 并生成缩略图。"""

import io
from pathlib import Path
from uuid import uuid4

from PIL import Image, UnidentifiedImageError

from app.core.config import settings
from app.core.errors import ValidationError
from app.services.clock import now

ALLOWED_MIME = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/gif": (b"GIF87a", b"GIF89a"),
    "image/webp": (b"RIFF",),
}

MAX_EDGE = 2000
THUMB_WIDTH = 400
QUALITY = 82


def _sniff(head: bytes) -> str | None:
    for mime, magics in ALLOWED_MIME.items():
        if any(head.startswith(magic) for magic in magics):
            return mime
    return None


def _prepare_dir() -> Path:
    stamp = now()
    target = Path(settings.upload_dir) / f"{stamp.year:04d}" / f"{stamp.month:02d}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def save_image(data: bytes, declared_mime: str | None) -> dict:
    if not data:
        raise ValidationError("文件为空")
    if len(data) > settings.upload_max_bytes:
        raise ValidationError(f"图片超过 {settings.upload_max_mb}MB 限制")

    sniffed = _sniff(data[:16])
    if sniffed is None:
        raise ValidationError("不支持的图片格式")
    if declared_mime and declared_mime not in ALLOWED_MIME:
        raise ValidationError("不支持的图片类型")
    if declared_mime and sniffed != declared_mime and not (
        declared_mime == "image/jpeg" and sniffed == "image/jpeg"
    ):
        raise ValidationError("文件内容与声明的类型不一致")

    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationError("图片无法解析") from exc

    if max(img.size) > MAX_EDGE:
        img.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)

    has_alpha = img.mode in ("RGBA", "LA", "P")
    converted = img.convert("RGBA" if has_alpha else "RGB")

    target_dir = _prepare_dir()
    stem = uuid4().hex
    main_name = f"{stem}.webp"
    thumb_name = f"thumb-{stem}.webp"

    converted.save(target_dir / main_name, "WEBP", quality=QUALITY, method=4)

    thumb = converted.copy()
    width = min(THUMB_WIDTH, thumb.width)
    ratio = width / thumb.width
    thumb = thumb.resize((width, max(1, int(thumb.height * ratio))), Image.LANCZOS)
    thumb.save(target_dir / thumb_name, "WEBP", quality=78, method=4)

    rel_dir = target_dir.relative_to(Path(settings.upload_dir)).as_posix()
    return {
        "url": f"/uploads/{rel_dir}/{main_name}",
        "thumb_url": f"/uploads/{rel_dir}/{thumb_name}",
        "width": converted.width,
        "height": converted.height,
        "bytes": len(data),
    }


def delete_image(url: str) -> None:
    """仅允许删除 uploads 下的文件，防路径穿越。"""
    prefix = "/uploads/"
    if not url.startswith(prefix):
        return
    relative = url[len(prefix) :]
    if ".." in relative:
        return
    base = Path(settings.upload_dir).resolve()
    target = (base / relative).resolve()
    if not str(target).startswith(str(base)):
        return
    target.unlink(missing_ok=True)
