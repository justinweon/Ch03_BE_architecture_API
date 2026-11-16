"""업로드 이미지 저장소. 파일은 UPLOAD_DIR 에 무작위 이름으로 저장하고 DB 에는 파일명만 기록한다."""
import uuid
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import PayloadTooLargeError, UnsupportedMediaTypeError

# 파일 앞부분(매직 넘버)으로 실제 형식을 확인한다. 클라이언트가 보낸 Content-Type 이나 확장자는 믿지 않는다.
_SIGNATURES = {
    b"\xff\xd8\xff": ".jpg",
    b"\x89PNG\r\n\x1a\n": ".png",
    b"GIF87a": ".gif",
    b"GIF89a": ".gif",
}


def _detect_extension(data: bytes) -> str | None:
    for signature, ext in _SIGNATURES.items():
        if data.startswith(signature):
            return ext
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


def upload_dir() -> Path:
    path = Path(settings.UPLOAD_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_image(data: bytes) -> str:
    if len(data) > settings.MAX_UPLOAD_BYTES:
        limit_mb = settings.MAX_UPLOAD_BYTES // (1024 * 1024)
        raise PayloadTooLargeError(f"이미지는 {limit_mb}MB 이하만 올릴 수 있습니다.")
    ext = _detect_extension(data)
    if ext is None:
        raise UnsupportedMediaTypeError("JPG, PNG, GIF, WEBP 이미지만 올릴 수 있습니다.")
    name = f"{uuid.uuid4().hex}{ext}"
    (upload_dir() / name).write_bytes(data)
    return name


def delete_image(name: str | None) -> None:
    if not name:
        return
    # 저장할 때 만든 파일명만 지운다 (경로 조작 방지)
    (upload_dir() / Path(name).name).unlink(missing_ok=True)
