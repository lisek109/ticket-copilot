import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.db.deps import get_db
from app.db import models
from app.api.schemas import TicketCreate, TicketOut, PredictionOut
from app.core.classifier import classify_ticket
from app.core.utils import sha256_text
from app.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/tickets", response_model=TicketOut)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user),):
    """Create a new ticket (email/web request)."""
    logger.info("Create ticket request received user_id=%s channel=%s", current_user.id, payload.channel)
    ticket = models.Ticket(
        channel=payload.channel,
        subject=payload.subject,
        body=payload.body,
        owner_id=current_user.id
    )
    
    logger.info("Ticket created ticket_id=%s owner_id=%s", ticket.id, current_user.id)
    
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user),):
    """Fetch ticket by id."""
    
    logger.info("Get ticket request ticket_id=%s user_id=%s", ticket_id, current_user.id)
    
    ticket = db.get(models.Ticket, ticket_id)
    if not ticket:
        logger.warning("Ticket not found ticket_id=%s user_id=%s", ticket_id, current_user.id)
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if ticket.owner_id != current_user.id:
        logger.warning("Access denied ticket_id=%s owner_id=%s requester_id=%s", ticket.id, ticket.owner_id, current_user.id)
        raise HTTPException(status_code=403, detail="Access denied")
    
    return ticket


@router.post("/tickets/{ticket_id}/classify", response_model=PredictionOut)
def classify(ticket_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user),):
    """
    Run classification for a ticket.
    Stores prediction + audit log.
    """
    
    logger.info("Classification requested ticket_id=%s user_id=%s", ticket_id, current_user.id)
    
    ticket = db.get(models.Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if ticket.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    request_id = str(uuid.uuid4())
    result = classify_ticket(ticket.subject or "", ticket.body or "")
    
    logger.info(
        "Classification completed ticket_id=%s category=%s priority=%s model=%s",
        ticket_id,
        result.category,
        result.priority,
        result.model_version,
    )

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
from app.llm.synthesis import synthesize_answer

@router.post("/tickets/{ticket_id}/answer")
def suggest_answer(ticket_id: str, db: Session = Depends(get_db),current_user=Depends(get_current_user),):
    
    logger.info("Answer generation requested ticket_id=%s user_id=%s", ticket_id, current_user.id)
    
    ticket = db.get(models.Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if ticket.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    ticket_text = f"{ticket.subject}\n{ticket.body}"

    try:
        result = rag_answer(ticket_text)
    except IndexNotReadyError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Try LLM synthesis; fallback to extractive answer if not configured
    llm_answer = synthesize_answer(ticket_text, result["sources"])
    final_answer = llm_answer if llm_answer else result["answer"]
    
    logger.info(
        "Answer generated ticket_id=%s answer_mode=%s sources=%s",
        ticket_id,
        "llm" if llm_answer else "extractive",
        len(result["sources"]),
    )

    return {
        "ticket_id": ticket.id,
        "suggested_answer": final_answer,
        "sources": result["sources"],
        "answer_mode": "llm" if llm_answer else "extractive",  
    }
