from __future__ import annotations

from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

# Static dataset representing the active patient census.
PATIENT_CENSUS: list[dict[str, Any]] = [
    {
        "patient_id": "WS-001",
        "name": "Margaret Chen",
        "dob": "1953-04-12",
        "age": 72,
        "address": {
            "street": "2847 N Clark St",
            "city": "Chicago",
            "state": "IL",
            "zip": "60657",
            "neighborhood": "Lincoln Park",
        },
        "diagnoses": ["Heart Failure (HFrEF)", "Chronic Kidney Disease Stage 3"],
        "caregiver_name": "Rosa Martinez",
        "visit_frequency": "3x/week",
        "last_ed_visit": "2025-02-03",
        "hospitalization_flag": True,
        "hospitalization_reason": "Acute decompensated heart failure",
        "open_care_plan_gaps": [
            "Medication reconciliation overdue (14 days)",
            "Daily weight monitoring not documented last 5 days",
            "Fluid restriction education not completed",
        ],
        "current_medications": [
            "Furosemide 40mg PO daily",
            "Carvedilol 6.25mg PO BID",
            "Lisinopril 10mg PO daily",
            "Spironolactone 25mg PO daily",
        ],
        "next_scheduled_visit": "2026-02-28",
        "risk_level": "HIGH",
        "risk_factors": [
            "Recent hospitalization",
            "HbA1c not tested in 6 months",
            "Diuretic compliance concern",
        ],
    },
    {
        "patient_id": "WS-002",
        "name": "Robert Hayes",
        "dob": "1957-09-28",
        "age": 68,
        "address": {
            "street": "1420 S Michigan Ave",
            "city": "Chicago",
            "state": "IL",
            "zip": "60605",
            "neighborhood": "South Loop",
        },
        "diagnoses": ["Type 2 Diabetes Mellitus", "Essential Hypertension"],
        "caregiver_name": "James Okafor",
        "visit_frequency": "2x/week",
        "last_ed_visit": "2025-01-19",
        "hospitalization_flag": True,
        "hospitalization_reason": "Hypertensive urgency with blood glucose 480 mg/dL",
        "open_care_plan_gaps": [
            "HbA1c recheck not scheduled",
            "Diabetic foot exam overdue (90 days)",
            "Home glucose log not reviewed in 3 weeks",
        ],
        "current_medications": [
            "Metformin 1000mg PO BID",
            "Insulin Glargine 30 units SC nightly",
            "Amlodipine 10mg PO daily",
            "Metoprolol 50mg PO BID",
        ],
        "next_scheduled_visit": "2026-03-01",
        "risk_level": "HIGH",
        "risk_factors": [
            "Uncontrolled diabetes",
            "Recent ED visit for hyperglycemia",
            "Hypertension not at goal",
        ],
    },
    {
        "patient_id": "WS-003",
        "name": "Dorothy Williams",
        "dob": "1946-11-05",
        "age": 79,
        "address": {
            "street": "5312 N Sheridan Rd",
            "city": "Chicago",
            "state": "IL",
            "zip": "60640",
            "neighborhood": "Edgewater",
        },
        "diagnoses": ["Heart Failure (HFpEF)", "Chronic Obstructive Pulmonary Disease"],
        "caregiver_name": "Linda Kowalczyk",
        "visit_frequency": "3x/week",
        "last_ed_visit": "2025-02-10",
        "hospitalization_flag": True,
        "hospitalization_reason": "COPD exacerbation with fluid overload",
        "open_care_plan_gaps": [
            "Inhaler technique reassessment due",
            "Oxygen therapy compliance not documented",
            "Advance directive review pending",
        ],
        "current_medications": [
            "Tiotropium inhaler daily",
            "Albuterol PRN",
            "Budesonide/Formoterol inhaler BID",
            "Torsemide 20mg PO daily",
        ],
        "next_scheduled_visit": "2026-02-28",
        "risk_level": "HIGH",
        "risk_factors": [
            "Dual cardiopulmonary diagnosis",
            "Frequent ED utilization",
            "Advanced age with functional decline",
        ],
    },
    {
        "patient_id": "WS-004",
        "name": "James Kowalski",
        "dob": "1960-03-17",
        "age": 65,
        "address": {
            "street": "3201 W Fullerton Ave",
            "city": "Chicago",
            "state": "IL",
            "zip": "60647",
            "neighborhood": "Logan Square",
        },
        "diagnoses": ["Type 2 Diabetes Mellitus"],
        "caregiver_name": "Angela Reyes",
        "visit_frequency": "1x/week",
        "last_ed_visit": None,
        "hospitalization_flag": False,
        "hospitalization_reason": None,
        "open_care_plan_gaps": [
            "Annual eye exam not scheduled",
            "Nephropathy screening (urine microalbumin) overdue",
        ],
        "current_medications": ["Metformin 500mg PO BID", "Sitagliptin 100mg PO daily"],
        "next_scheduled_visit": "2026-03-04",
        "risk_level": "MEDIUM",
        "risk_factors": ["HbA1c trending up (7.8 → 8.4)", "HEDIS screening gaps"],
    },
    {
        "patient_id": "WS-005",
        "name": "Patricia Santos",
        "dob": "1951-07-22",
        "age": 74,
        "address": {
            "street": "4450 N Broadway",
            "city": "Chicago",
            "state": "IL",
            "zip": "60640",
            "neighborhood": "Uptown",
        },
        "diagnoses": ["Essential Hypertension", "Chronic Kidney Disease Stage 2"],
        "caregiver_name": "Maria Delgado",
        "visit_frequency": "1x/week",
        "last_ed_visit": None,
        "hospitalization_flag": False,
        "hospitalization_reason": None,
        "open_care_plan_gaps": [
            "CKD dietary counseling not completed",
            "Blood pressure trending above goal last 3 visits",
        ],
        "current_medications": [
            "Losartan 100mg PO daily",
            "Hydrochlorothiazide 25mg PO daily",
            "Atorvastatin 40mg PO nightly",
        ],
        "next_scheduled_visit": "2026-03-05",
        "risk_level": "MEDIUM",
        "risk_factors": ["BP not at goal", "CKD progression risk", "Medication adherence concern"],
    },
    {
        "patient_id": "WS-006",
        "name": "Harold Nguyen",
        "dob": "1944-08-30",
        "age": 81,
        "address": {
            "street": "6710 N Sheridan Rd",
            "city": "Chicago",
            "state": "IL",
            "zip": "60626",
            "neighborhood": "Rogers Park",
        },
        "diagnoses": ["Heart Failure (HFpEF)"],
        "caregiver_name": "Thomas Chen",
        "visit_frequency": "2x/week",
        "last_ed_visit": "2025-10-15",
        "hospitalization_flag": False,
        "hospitalization_reason": None,
        "open_care_plan_gaps": ["Fall risk reassessment due"],
        "current_medications": ["Furosemide 20mg PO daily", "Ramipril 5mg PO daily"],
        "next_scheduled_visit": "2026-03-02",
        "risk_level": "LOW",
        "risk_factors": ["Advanced age", "Fall risk"],
    },
]


def _apply_filter(filter_value: str | None) -> list[dict[str, Any]]:
    f = (filter_value or "all").lower()
    if f not in {"all", "high_risk", "hospitalization_flag"}:
        raise ValueError("Invalid filter. Expected one of: all, high_risk, hospitalization_flag.")
    if f == "all":
        return PATIENT_CENSUS
    if f == "high_risk":
        return [p for p in PATIENT_CENSUS if p.get("risk_level") == "HIGH"]
    # hospitalization_flag
    return [p for p in PATIENT_CENSUS if bool(p.get("hospitalization_flag"))]


def register(server: FastMCP) -> None:
    """
    Register the census tool with the provided MCP server.
    Exposes:
      - get_active_patient_census(filter?: "all" | "high_risk" | "hospitalization_flag")
    """

    @server.tool(
        name="get_active_patient_census",
        description=(
            "Retrieves the active home care patient census from WellSky. Returns all patients with "
            "open care plans, hospitalization flags, upcoming visits, caregiver assignments, and risk levels."
        ),
    )
    def get_active_patient_census(filter: Optional[str] = "all") -> dict[str, Any]:
        data = _apply_filter(filter)
        # Return JSON content to align with FastMCP json_response behavior.
        return {
            "content": [
                {"type": "json", "json": data},
            ]
        }

    return None
