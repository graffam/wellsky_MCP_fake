from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, root_validator, validator

OutreachChannel = Literal["phone", "sms", "email"]
OutreachStatus = Literal["queued", "needs_manual_review"]


class ContactInfo(BaseModel):
    phone: Optional[str] = Field(None, min_length=7)
    sms: Optional[str] = Field(None, min_length=7)
    email: Optional[EmailStr] = None

    @root_validator
    def ensure_at_least_one_contact(cls, values: dict[str, Optional[str]]) -> dict[str, Optional[str]]:
        if not any(values.get(field) for field in ("phone", "sms", "email")):
            raise ValueError(
                "Provide at least one reachable contact method (phone, sms, or email)."
            )
        return values


class Patient(BaseModel):
    id: str
    fullName: str
    preferredChannel: Optional[OutreachChannel] = None
    contacts: ContactInfo
    carePlanSummary: Optional[str] = Field(None, max_length=280)
    notes: Optional[str] = Field(None, max_length=500)

    @validator("id", "fullName")
    def non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("This field cannot be empty.")
        return value


class ReachOutInput(BaseModel):
    patients: list[Patient] = Field(..., min_items=1)
    messageTemplate: Optional[str] = Field(None, max_length=500)
    fallbackChannel: Optional[OutreachChannel] = None


class OutreachOutcome(BaseModel):
    patientId: str
    fullName: str
    engagementId: str
    status: OutreachStatus
    channel: Literal["phone", "sms", "email", "unavailable"]
    summary: str
    messagePreview: Optional[str] = None
    reason: Optional[str] = None
    timestamp: str


class OutreachMetadata(BaseModel):
    integration: str
    durationMs: int
    startedAt: str


class OutreachResponse(BaseModel):
    outcomes: list[OutreachOutcome]
    metadata: OutreachMetadata
