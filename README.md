# WellSky Outreach MCP Server (Python on Vercel)

This project delivers a Model Context Protocol (MCP) server implemented with FastMCP (the reference server from the `mcp` Python package) and deployed via Vercel’s Python runtime. The lone tool, `reach_out_to_patients`, accepts a batch of patient records and produces an outreach report.

## Prerequisites

- Python 3.11+
- `pip` (or `uv`, `pipenv`, etc.) for dependency management
- A Vercel account with the [Vercel CLI](https://vercel.com/docs/cli) authenticated locally

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.app:app --reload
```

The server listens on `http://localhost:8000`. Call `POST /mcp` (or simply `POST /`) to exercise the tool; both paths map to the same FastMCP transport.

Example MCP request body:

```jsonc
{
  "id": "reach-out-demo",
  "method": "tools.call",
  "params": {
    "name": "reach_out_to_patients",
    "arguments": {
      "patients": [
        {
          "id": "12345",
          "fullName": "Alex Johnson",
          "preferredChannel": "sms",
          "contacts": {
            "sms": "+15551234567",
            "email": "alex.johnson@example.com"
          }
        }
      ],
      "messageTemplate": "Hello {fullName}, this is your WellSky care team checking in."
    }
  }
}
```

The response mirrors the MCP server contract: a text summary plus structured JSON describing each outreach record.

## Deployment to Vercel

1. Ensure the MCP dependencies are available to Vercel by committing `requirements.txt`.
2. Link the project:
   ```bash
   vercel link
   ```
3. Deploy:
   ```bash
   vercel deploy --prod
   ```

Vercel automatically detects the Python runtime for any `api/*.py` file. The included `vercel.json` maps `/api/mcp` to the FastMCP Starlette wrapper. No environment variables are required.

## Tool Contract

- **Tool name:** `reach_out_to_patients`
- **Description:** Hands patient outreach tasks to WellSky’s engagement services.
- **Input schema (simplified):**
  - `patients[]` – required array
    - `id` – string
    - `fullName` – string
    - `contacts` – at least one of `phone`, `sms`, or `email`
    - Optional: `preferredChannel`, `carePlanSummary`, `notes`
  - Optional: `messageTemplate`, `fallbackChannel`
- **Output:** Text summary plus JSON payload with `outcomes[]` and job metadata.
