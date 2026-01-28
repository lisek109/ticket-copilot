import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.db import models
from app.api.schemas import TicketCreate, TicketOut, PredictionOut
from app.core.classifier import classify_ticket
from app.core.utils import sha256_text

router = APIRouter()

@router.post("/tickets", response_model=TicketOut)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    """Create a new ticket (email/web request)."""
    ticket = models.Ticket(
        channel=payload.channel,
        subject=payload.subject,
        body=payload.body
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

@router.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    """Fetch ticket by id."""
    ticket = db.get(models.Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@router.post("/tickets/{ticket_id}/classify", response_model=PredictionOut)
def classify(ticket_id: str, db: Session = Depends(get_db)):
    """
    Run classification for a ticket.
    Stores prediction + audit log.
    """
    ticket = db.get(models.Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    request_id = str(uuid.uuid4())
    result = classify_ticket(ticket.subject or "", ticket.body or "")

    # Store prediction
    pred = models.TicketPrediction(
        ticket_id=ticket.id,
        category=result.category,
        priority=result.priority,
        confidence=result.confidence,
        model_version=result.model_version,
    )
    db.add(pred)

    # Store audit log (input is hashed, not stored in raw form)
    input_hash = sha256_text(f"{ticket.subject}\n{ticket.body}")
    audit = models.AuditLog(
        request_id=request_id,
        action="ticket.classify",
        actor="anonymous",
        input_hash=input_hash,
        details=(
            f"category={result.category};"
            f"priority={result.priority};"
            f"confidence={result.confidence};"
            f"model_version={result.model_version}"
        ),
    )
    db.add(audit)

    db.commit()
    return PredictionOut(**result.__dict__)



from app.rag.query import rag_answer, IndexNotReadyError

@router.post("/tickets/{ticket_id}/answer")
def suggest_answer(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.get(models.Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    question = f"{ticket.subject}\n{ticket.body}"
    
    try:
        result = rag_answer(question)
    except IndexNotReadyError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "ticket_id": ticket.id,
        "suggested_answer": result["answer"],
        "sources": result["sources"],
    }
