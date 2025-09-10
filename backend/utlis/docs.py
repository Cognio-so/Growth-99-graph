from pathlib import Path
from uuid import uuid4
import os

# Use a relative path for portability
UPLOAD_DIR = Path("./uploads")
LOGOS_DIR = UPLOAD_DIR / "logos"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
LOGOS_DIR.mkdir(parents=True, exist_ok=True)

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

async def save_logo_to_disk(upload_file, session_id: str = None) -> dict:
    """Save logo file to logos directory, create URL, and store in database."""
    ext = Path(upload_file.filename or "").suffix or ""
    fname = f"logo_{uuid4().hex}{ext}"
    fpath = LOGOS_DIR / fname

    with fpath.open("wb") as out:
        while True:
            chunk = await upload_file.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)

    # Create URL for the logo - use Railway URL in production, localhost in development
    # Railway automatically sets RAILWAY_PUBLIC_DOMAIN environment variable
    if os.getenv("RAILWAY_PUBLIC_DOMAIN"):
        # Production on Railway
        base_url = f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}"
    elif os.getenv("RAILWAY_STATIC_URL"):
        # Alternative Railway URL
        base_url = os.getenv("RAILWAY_STATIC_URL")
    else:
        # Development (localhost)
        base_url = "http://localhost:8000"
    
    logo_url = f"{base_url}/uploads/logos/{fname}"
    
    print(f"🖼️ Logo URL generated: {logo_url}")
    
    # Save logo information to database
    logo_data = {
        "name": upload_file.filename,
        "mime": upload_file.content_type or "application/octet-stream",
        "size": fpath.stat().st_size,
        "path": str(fpath),
        "url": logo_url,
        "filename": fname
    }
    
    # Store in database if session_id is provided
    if session_id:
        try:
            from datetime import datetime
            from sqlalchemy.orm import sessionmaker
            from db import engine
            from models import Logo
            import uuid

            # Create a session factory
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

            with SessionLocal() as db:
                logo_record = Logo(
                    id=f"logo_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}",
                    session_id=session_id,
                    filename=fname,
                    original_name=upload_file.filename or "unknown",
                    file_path=str(fpath),
                    url=logo_url,
                    mime_type=upload_file.content_type or "application/octet-stream",
                    file_size=fpath.stat().st_size,
                    meta={"upload_timestamp": datetime.now().isoformat()}
                )
                db.add(logo_record)
                db.commit()
                print(f"✅ Logo saved to database: {fname}")
        except Exception as e:
            print(f"⚠️ Failed to save logo to database: {e}")
    
    return logo_data
