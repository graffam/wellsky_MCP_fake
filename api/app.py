from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, Optional

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


def _format_json_rpc_error(
    message_id: Any, code: int, message: str, data: Any = None
) -> Dict[str, Any]:
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
        response = _handle_rpc_control_message(method, message_id, params)
        if response is None:
            error_payload = _format_json_rpc_error(
                message_id,
                code=-32601,
                message=f"Unsupported method '{method}'.",
            )
            return _sse_response(error_payload)
        return _sse_response(response)

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


def _handle_rpc_control_message(
    method: str, message_id: Optional[Any], params: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    if method == "initialize":
        capabilities = {
            "tools": {
                "list": True,
                "call": True,
            }
        }
        result = {
            "protocolVersion": "0.5",
            "serverInfo": {
                "name": "wellsky-outreach-mcp",
                "version": "0.2.0",
            },
            "capabilities": capabilities,
        }
        return _format_json_rpc_result(message_id, result)

    if method == "tools.list":
        tool_schema = _build_tool_json_schema()
        result = {
            "tools": [
                {
                    "name": "reach_out_to_patients",
                    "description": (
                        "Pretends to send outreach notifications to patients via WellSky's"
                        " care coordination services."
                    ),
                    "inputSchema": tool_schema,
                }
            ]
        }
        return _format_json_rpc_result(message_id, result)

    if method == "ping":
        return _format_json_rpc_result(message_id, {"message": "pong"})

    return None


def _build_tool_json_schema() -> Dict[str, Any]:
    contact_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "phone": {"type": "string", "minLength": 7},
            "sms": {"type": "string", "minLength": 7},
            "email": {"type": "string", "format": "email"},
        },
        "additionalProperties": False,
        "minProperties": 1,
    }

    patient_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "id": {"type": "string", "minLength": 1},
            "fullName": {"type": "string", "minLength": 1},
            "preferredChannel": {
                "type": "string",
                "enum": ["phone", "sms", "email"],
            },
            "contacts": contact_schema,
            "carePlanSummary": {
                "type": "string",
                "maxLength": 280,
            },
            "notes": {
                "type": "string",
                "maxLength": 500,
            },
        },
        "required": ["id", "fullName", "contacts"],
        "additionalProperties": False,
    }

    return {
        "type": "object",
        "properties": {
            "patients": {
                "type": "array",
                "items": patient_schema,
                "minItems": 1,
            },
            "messageTemplate": {
                "type": "string",
                "maxLength": 500,
            },
            "fallbackChannel": {
                "type": "string",
                "enum": ["phone", "sms", "email"],
            },
        },
        "required": ["patients"],
        "additionalProperties": False,
    }
