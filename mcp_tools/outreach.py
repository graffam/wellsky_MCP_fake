from __future__ import annotations

from typing import Any, Literal, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from wellsky_mcp import ReachOutInput, process_wellsky_outreach


def register(server: FastMCP) -> None:
    """Register the WellSky outreach tool with the provided MCP server."""

    @server.tool(
        name="reach_out_to_patients",
        description=(
            "Sends outreach notifications to patients via WellSky's care "
            "coordination services and returns a summary."
        ),
    )
    def reach_out_to_patients(
        patients: list[dict[str, Any]],
        messageTemplate: Optional[str] = None,
        fallbackChannel: Optional[Literal["phone", "sms", "email"]] = None,
    ) -> dict[str, Any]:
        try:
            payload = ReachOutInput(
                patients=patients,
                messageTemplate=messageTemplate,
                fallbackChannel=fallbackChannel,
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
