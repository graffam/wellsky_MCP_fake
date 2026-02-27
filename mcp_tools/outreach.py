from __future__ import annotations

from typing import Any, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from wellsky_mcp import ContactInfo, Patient, ReachOutInput, process_wellsky_outreach


def _mock_directory_lookup(patient_id: str) -> tuple[str, ContactInfo]:
    """
    Simulate an internal directory/service that can resolve a patient's
    full name and best contact methods from only a patient ID.
    """
    # Derive deterministic but fake contact info from the ID (for demo purposes).
    digits = "".join(ch for ch in patient_id if ch.isdigit()) or "0000"
    last4 = digits[-4:].rjust(4, "0")

    # Ensure phone/sms meet the min_length=7 requirement in ContactInfo
    phone = f"555010{last4}"  # e.g., 5550101234
    sms = phone
    email_local = "".join(ch for ch in patient_id.lower() if ch.isalnum()) or "patient"
    email = f"{email_local}@example.com"

    # Also provide a somewhat friendly full name
    full_name = f"Patient {patient_id}"

    contacts = ContactInfo(phone=phone, sms=sms, email=email)
    return full_name, contacts


def _auto_resolve_patients(patient_ids: list[str]) -> list[Patient]:
    resolved: list[Patient] = []
    for pid in patient_ids:
        full_name, contacts = _mock_directory_lookup(pid)
        resolved.append(
            Patient(
                id=pid,
                fullName=full_name,
                contacts=contacts,
                # preferredChannel intentionally omitted to let the simulator choose
            )
        )
    return resolved


def register(server: FastMCP) -> None:
    """Register the WellSky outreach tool with the provided MCP server."""

    @server.tool(
        name="reach_out_to_patients",
        description=(
            "Sends outreach notifications for a list of patient IDs using an internal directory "
            "to auto-resolve names and contact information. Only patientIds and an optional "
            "message are required. Returns a summary."
        ),
    )
    def reach_out_to_patients(
        patientIds: list[str],
        message: Optional[str] = None,
    ) -> dict[str, Any]:
        try:
            # Auto-resolve patients from IDs (pretend the MCP/server has access)
            patients = _auto_resolve_patients(patientIds)

            payload = ReachOutInput(
                patients=patients,
                messageTemplate=message,
                fallbackChannel=None,  # Let the simulator resolve based on available contacts
            )
        except ValidationError as exc:
            raise ValueError(f"Invalid outreach request: {exc}") from exc

        job = process_wellsky_outreach(payload)

        queued = sum(1 for outcome in job.outcomes if outcome.status == "queued")
        manual = len(job.outcomes) - queued

        summary_lines = [
            f"- {outcome.fullName} ({outcome.patientId}) -> "
            + (
                f"Queued via {outcome.channel.upper()}"
                if outcome.status == "queued"
                else f"Manual review required: {outcome.reason or 'unspecified'}"
            )
            for outcome in job.outcomes
        ]

        text_summary = "\n".join(
            [
                f"Hand-off to WellSky Outreach on {job.metadata.startedAt}.",
                f"Queued: {queued} | Needs manual review: {manual}.",
                "",
                *summary_lines,
            ]
        )

        return {
            "content": [
                {"type": "text", "text": text_summary},
                {"type": "json", "json": job.dict()},
            ]
        }

    return None
