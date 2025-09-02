from pathlib import Path
from uuid import uuid4

# Use a relative path for portability
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

async def save_upload_to_disk(upload_file) -> dict:
    ext = Path(upload_file.filename or "").suffix or ""
    fname = f"{uuid4().hex}{ext}"
    fpath = UPLOAD_DIR / fname

    with fpath.open("wb") as out:
        while True:
            chunk = await upload_file.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)

    return {
        "name": upload_file.filename,
        "mime": upload_file.content_type or "application/octet-stream",
        "size": fpath.stat().st_size,
        "path": str(fpath),
    }
