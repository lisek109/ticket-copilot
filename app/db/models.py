import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

def gen_uuid() -> str:
    return str(uuid.uuid4())

class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Minimal fields for MVP
    channel: Mapped[str] = mapped_column(String(20), default="email")  # email/web
    subject: Mapped[str] = mapped_column(String(300), default="")
    body: Mapped[str] = mapped_column(Text)

    predictions: Mapped[list["TicketPrediction"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan"
    )

class TicketPrediction(Base):
    __tablename__ = "ticket_predictions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    ticket_id: Mapped[str] = mapped_column(String(36), ForeignKey("tickets.id"), index=True)

    # Prediction outputs (will be produced by ML )
    category: Mapped[str] = mapped_column(String(80))
    priority: Mapped[int] = mapped_column(Integer)   # 1..4
    confidence: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(40), default="rules-v0")

    ticket: Mapped["Ticket"] = relationship(back_populates="predictions")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # A correlation id for tracing one request across components
    request_id: Mapped[str] = mapped_column(String(36), index=True)

    # What happened (e.g. "ticket.classify")
    action: Mapped[str] = mapped_column(String(60))

    # Who triggered it 
    actor: Mapped[str] = mapped_column(String(120), default="anonymous")

    # Hash of input text (do NOT store raw text in audit logs)
    input_hash: Mapped[str] = mapped_column(String(64), default="")

    # Free-form details for debugging (safe, no secrets)
    details: Mapped[str] = mapped_column(Text, default="")
