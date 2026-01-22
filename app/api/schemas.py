from pydantic import BaseModel, Field, ConfigDict

class TicketCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    channel: str = Field(default="email")
    subject: str = Field(default="")
    body: str

class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    id: str
    channel: str
    subject: str
    body: str

class PredictionOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    category: str
    priority: int
    confidence: float
    model_version: str
