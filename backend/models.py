# models.py
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, JSON, Text, ForeignKey, Integer, Boolean

class Base(DeclarativeBase):
    pass

class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

class Message(Base):
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))  # user | assistant | system
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

class Logo(Base):
    __tablename__ = "logos"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("sessions.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    original_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

class ConversationHistory(Base):
    __tablename__ = "conversation_history"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("sessions.id"), index=True)
    message_id: Mapped[str] = mapped_column(String(80), ForeignKey("messages.id"), index=True)
    user_query: Mapped[str] = mapped_column(Text)
    ai_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    sandbox_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    generation_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_edit: Mapped[bool] = mapped_column(Boolean, default=False)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

class SessionGeneratedLinks(Base):
    __tablename__ = "session_generated_links"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("sessions.id"), index=True)
    conversation_id: Mapped[str] = mapped_column(String(80), ForeignKey("conversation_history.id"), index=True)
    sandbox_url: Mapped[str] = mapped_column(String(500))
    generated_code: Mapped[str] = mapped_column(Text)
    generation_number: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
