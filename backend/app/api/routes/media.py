"""评论配图：上传 / 读取 / 删除自己的图。

存储刻意保持「一个文件 + 一行元数据」：
  · 文件写到 `settings.media_dir/<id>.<ext>`，id 是 32 位 uuid hex；
  · 数据库只记归属、类型、大小，方便按用户清理；
  · 不信任客户端的 Content-Type：同时检查声明类型与文件头（magic），
    两者必须一致且在白名单内，避免把 html/svg 伪装成图片挂到站内域名下。
"""
from __future__ import annotations

import pathlib
import re
import uuid

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import select

from ...core.config import settings
from ...models import Media
from ...schemas import MediaOut
from ..deps import CurrentUser, Db, VerifiedUser, rate_limit

router = APIRouter(prefix="/media", tags=["media"])

#: 允许的图片类型 → 规范扩展名
ALLOWED: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
#: 浏览器/客户端偶尔会带这些别名
ALIASES = {"image/jpg": "image/jpeg", "image/pjpeg": "image/jpeg",
           "image/x-png": "image/png"}
_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_CHUNK = 64 * 1024


def _sniff(data: bytes) -> str | None:
    """按文件头判断真实类型；识别不出返回 None。"""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def _url(media_id: str) -> str:
    return f"{settings.api_v1}/media/{media_id}"


def _path(m: Media) -> pathlib.Path:
    return settings.media_dir / m.filename


@router.post("", response_model=MediaOut, status_code=201)
async def upload(request: Request, user: VerifiedUser, db: Db,
                 file: UploadFile = File(...)):
    """上传一张图（jpeg / png / webp，≤ 5 MB）。"""
    rate_limit(request, "media", 60, user.id)

    declared = (file.content_type or "").split(";")[0].strip().lower()
    declared = ALIASES.get(declared, declared)
    if declared not in ALLOWED:
        raise HTTPException(415, "只支持 JPEG / PNG / WebP 图片")

    limit = settings.media_max_bytes
    chunks: list[bytes] = []
    size = 0
    while True:
        chunk = await file.read(_CHUNK)
        if not chunk:
            break
        size += len(chunk)
        if size > limit:
            raise HTTPException(413, f"图片不能超过 {limit // (1024 * 1024)} MB")
        chunks.append(chunk)
    await file.close()

    data = b"".join(chunks)
    if not data:
        raise HTTPException(422, "图片是空的")

    actual = _sniff(data[:32])
    if actual is None:
        raise HTTPException(415, "无法识别的图片格式")
    if actual != declared:
        raise HTTPException(415, "文件内容与声明的图片类型不一致")

    media_id = uuid.uuid4().hex
    filename = f"{media_id}{ALLOWED[actual]}"
    settings.media_dir.mkdir(parents=True, exist_ok=True)
    path = settings.media_dir / filename
    try:
        with open(path, "xb") as fh:
            fh.write(data)
    except FileExistsError as exc:              # pragma: no cover - uuid 碰撞
        raise HTTPException(409, "请重试") from exc

    m = Media(id=media_id, user_id=user.id, filename=filename,
              original_name=(file.filename or "")[:200],
              content_type=actual, size=size)
    db.add(m)
    db.commit()
    db.refresh(m)
    return MediaOut(id=m.id, url=_url(m.id), content_type=m.content_type,
                    size=m.size)


@router.get("/{media_id}")
def get_media(media_id: str, db: Db):
    """公开读取：评论里的图片要能在未登录时显示。"""
    if not _ID_RE.match(media_id):
        raise HTTPException(404, "图片不存在")
    m = db.get(Media, media_id)
    if m is None:
        raise HTTPException(404, "图片不存在")
    path = _path(m)
    if not path.is_file():
        raise HTTPException(404, "图片文件已丢失")
    return FileResponse(path, media_type=m.content_type,
                        headers={
                            # 内容不可变（id 唯一），可以长缓存
                            "Cache-Control": "public, max-age=31536000, immutable",
                            "X-Content-Type-Options": "nosniff",
                        })


@router.delete("/{media_id}", status_code=204)
def delete_media(media_id: str, user: CurrentUser, db: Db):
    """删除自己的媒体（可选能力，供控制台清理）。"""
    if not _ID_RE.match(media_id):
        raise HTTPException(404, "图片不存在")
    m = db.get(Media, media_id)
    if m is None:
        raise HTTPException(404, "图片不存在")
    if m.user_id != user.id and not user.is_staff:
        raise HTTPException(403, "只能删除自己上传的图片")
    try:
        _path(m).unlink(missing_ok=True)
    except OSError:
        pass                      # 文件已丢也要把元数据清掉
    db.delete(m)
    db.commit()
    return None


@router.get("", include_in_schema=False)
def list_own(user: CurrentUser, db: Db):
    """自己的上传列表（控制台用；不在公开文档里）。"""
    rows = db.exec(select(Media).where(Media.user_id == user.id)
                   .order_by(Media.created_at.desc()).limit(100)).all()
    return {"items": [{"id": m.id, "url": _url(m.id),
                       "content_type": m.content_type, "size": m.size}
                      for m in rows]}
