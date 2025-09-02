# schemas.py
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class UserQueryIn(BaseModel):
    session_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    text: str = Field(..., min_length=1)      # query or URL
    llm_model: Optional[str] = None           # e.g., "gpt-4o", "gpt-4o-mini"

class UserQueryOut(BaseModel):
    session_id: str
    accepted: bool
    state: Dict[str, Any]
