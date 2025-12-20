from pydantic import BaseModel, Field

class TicketCreate(BaseModel):
    channel: str = Field(default="email")
    subject: str = Field(default="")
    body: str

class TicketOut(BaseModel):
    id: str
    channel: str
    subject: str
    body: str

    class Config:
        from_attributes = True

class PredictionOut(BaseModel):
    category: str
    priority: int
    confidence: float
    model_version: str
