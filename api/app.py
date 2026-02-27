from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import ValidationError

from wellsky_mcp import ReachOutInput, simulate_wellsky_outreach

app = FastAPI(
    title="WellSky Outreach MCP Simulator",
    version="0.1.0",
    description="Pretend MCP tool that simulates patient outreach via WellSky.",
)


@app.get("/")
async def index():
    return {
        "status": "ok",
        "message": "Use POST / or POST /api/mcp for MCP tool calls.",
    }


@app.get("/api/mcp")
async def mcp_health():
    return {"status": "ok", "message": "POST to this path to call reach_out_to_patients."}


def _build_tool_result(parsed: ReachOutInput) -> Dict[str, Any]:
    simulation = simulate_wellsky_outreach(parsed)

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

    return {
        "content": [
            {"type": "text", "text": text_summary},
            {"type": "json", "json": simulation.dict()},
        ]
    }


def _format_json_rpc_result(message_id: Any, result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": message_id,
        "result": result,
    }


def _format_json_rpc_error(message_id: Any, code: int, message: str, data: Any = None) -> Dict[str, Any]:
    error: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": message_id, "error": error}


def _sse_response(payload: Dict[str, Any]) -> StreamingResponse:
    async def event_stream() -> AsyncIterator[str]:
        yield f"data: {json.dumps(payload)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.post("/")
@app.post("/api/mcp")
async def reach_out_to_patients(request: Request):
    try:
        raw_payload = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Request body must be JSON.") from exc

    is_json_rpc = isinstance(raw_payload, dict) and "method" in raw_payload

    if not is_json_rpc:
        try:
            parsed = ReachOutInput(**raw_payload)
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=exc.errors()) from exc

        return JSONResponse(_build_tool_result(parsed))

    message_id = raw_payload.get("id")
    method = raw_payload.get("method")
    params = raw_payload.get("params", {})

    if method != "tools.call":
        error_payload = _format_json_rpc_error(
            message_id,
            code=-32601,
            message=f"Unsupported method '{method}'.",
        )
        return _sse_response(error_payload)

    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    if tool_name != "reach_out_to_patients":
        error_payload = _format_json_rpc_error(
            message_id,
            code=-32601,
            message=f"Unknown tool '{tool_name}'.",
        )
        return _sse_response(error_payload)

    try:
        parsed = ReachOutInput(**arguments)
    except ValidationError as exc:
        error_payload = _format_json_rpc_error(
            message_id,
            code=-32602,
            message="Invalid tool arguments.",
            data=exc.errors(),
        )
        return _sse_response(error_payload)

    result_payload = _build_tool_result(parsed)

    json_rpc_response = _format_json_rpc_result(
        message_id,
        result_payload,
    )

    return _sse_response(json_rpc_response)
