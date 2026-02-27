from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from wellsky_mcp import ReachOutInput, simulate_wellsky_outreach

app = FastAPI(
    title="WellSky Outreach MCP Simulator",
    version="0.1.0",
    description="Pretend MCP tool that simulates patient outreach via WellSky.",
)


@app.get("/")
async def index():
    return {"status": "ok", "message": "Use POST / or POST /api/mcp for MCP tool calls."}


@app.get("/api/mcp")
async def mcp_health():
    return {"status": "ok", "message": "POST to this path to call reach_out_to_patients."}


@app.post("/")
@app.post("/api/mcp")
async def reach_out_to_patients(payload: ReachOutInput):
    try:
        simulation = simulate_wellsky_outreach(payload)
    except ValueError as exc:  # bubble up validation from nested models
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    queued = sum(1 for outcome in simulation.outcomes if outcome.status == "queued")
    manual = len(simulation.outcomes) - queued

    summary_lines = [
        f"- {outcome.fullName} ({outcome.patientId}) -> "
        + (
            f"Queued via {outcome.channel.upper()}"
            if outcome.status == "queued"
            else f"Manual review required: {outcome.reason or 'unspecified'}"
        )
        for outcome in simulation.outcomes
    ]

    text_summary = "\n".join(
        [
            f"Simulated hand-off to WellSky Outreach on {simulation.metadata.startedAt}.",
            f"Queued: {queued} | Needs manual review: {manual}.",
            "",
            *summary_lines,
        ]
    )

    return JSONResponse(
        {
            "content": [
                {"type": "text", "text": text_summary},
                {"type": "json", "json": simulation.dict()},
            ]
        }
    )
