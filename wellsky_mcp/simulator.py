from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Optional
from uuid import uuid4

from .models import (
    ContactInfo,
    OutreachMetadata,
    OutreachOutcome,
    OutreachResponse,
    OutreachStatus,
    OutreachChannel,
    Patient,
    ReachOutInput,
)

DEFAULT_TEMPLATE = (
    "Hello {fullName}, this is a care team check-in from WellSky. "
    "Reply if you need any support."
)


def _resolve_channel(
    patient: Patient,
    fallback_channel: Optional[OutreachChannel],
) -> tuple[OutreachStatus, str, str, Optional[str]]:
    contacts: ContactInfo = patient.contacts
    available = [(key, value) for key, value in contacts.dict().items() if value]

    preferred = next(
        ((channel, value) for channel, value in available if channel == patient.preferredChannel),
        None,
    )

    fallback = (
        next(((channel, value) for channel, value in available if channel == fallback_channel), None)
        if fallback_channel
        else None
    )

    chosen = preferred or fallback or (available[0] if available else None)

    if not chosen:
        return (
            "needs_manual_review",
            "unavailable",
            (
                "No viable contact channel detected. Escalated for manual follow-up."
            ),
            (
                "Patient record is missing reachable contact methods across phone, sms, and email."
            ),
        )

    channel, destination = chosen
    return (
        "queued",
        channel,
        f"Hand-off to WellSky Outreach via {channel.upper()} ({destination}).",
        None,
    )


def _build_outcomes(
    patients: Iterable[Patient],
    message_template: Optional[str],
    fallback_channel: Optional[OutreachChannel],
    started_at: datetime,
) -> list[OutreachOutcome]:
    outcomes: list[OutreachOutcome] = []
    template = message_template or DEFAULT_TEMPLATE

    for index, patient in enumerate(patients):
        message_preview = template.replace("{fullName}", patient.fullName)
        status, channel, summary, reason = _resolve_channel(patient, fallback_channel)

        outcomes.append(
            OutreachOutcome(
                patientId=patient.id,
                fullName=patient.fullName,
                engagementId=str(uuid4()),
                status=status,
                channel=channel,
                summary=summary,
                messagePreview=message_preview if status == "queued" else None,
                reason=reason,
                timestamp=(started_at.replace(microsecond=0).isoformat()),
            )
        )

    return outcomes


def process_wellsky_outreach(payload: ReachOutInput) -> OutreachResponse:
    """Process a WellSky outreach job."""
    started_at = datetime.now(tz=timezone.utc)
    outcomes = _build_outcomes(
        payload.patients,
        payload.messageTemplate,
        payload.fallbackChannel,
        started_at,
    )

    duration_ms = int((datetime.now(tz=timezone.utc) - started_at).total_seconds() * 1000)

    metadata = OutreachMetadata(
        integration="WellSky Patient Outreach",
        durationMs=duration_ms,
        startedAt=started_at.replace(microsecond=0).isoformat(),
    )

    return OutreachResponse(outcomes=outcomes, metadata=metadata)
