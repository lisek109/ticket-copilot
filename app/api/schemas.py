from pydantic import BaseModel, Field, ConfigDict

class TicketCreate(BaseModel):
    # Pydantic v2 config:
    # - disable protected "model_" namespace (for model_version elsewhere)
    model_config = ConfigDict(protected_namespaces=())

    # Input fields when creating a ticket (POST /tickets)
    channel: str = Field(default="email")   # e.g. email / web
    subject: str = Field(default="")        # optional subject line
    body: str                               # main ticket content (required)

class TicketOut(BaseModel):
    # Enable ORM -> schema conversion (SQLAlchemy model -> response)
    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=(),
    )

    # Fields returned to client when fetching a ticket
    id: str
    channel: str
    subject: str
    body: str

class PredictionOut(BaseModel):
    # Output schema for classification results
    model_config = ConfigDict(protected_namespaces=())

    category: str        # predicted category (access / incident / etc.)
    priority: int        # priority level (1 = highest)
    confidence: float    # model confidence (0.0 - 1.0)
    model_version: str   # which model produced the prediction
