from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .models import get_session, Pet, HealthLog
from .ai_service import check_symptoms, generate_report

router = APIRouter()

# -------------------------------------------------------------------
# Dependency that yields a DB session and ensures it is closed.
# -------------------------------------------------------------------
def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()

# -------------------------------------------------------------------
# Pydantic schemas for request / response payloads
# -------------------------------------------------------------------
class SymptomCheckRequest(BaseModel):
    pet_id: int
    symptom_text: str = Field(..., max_length=2000)
    photo_url: Optional[str] = None

class ConditionItem(BaseModel):
    name: str
    confidence: float
    urgency: str

class SymptomCheckResponse(BaseModel):
    conditions: List[ConditionItem]

class ReportRequest(BaseModel):
    pet_id: int
    start_date: datetime
    end_date: datetime

class ReportResponse(BaseModel):
    report_text: str

# -------------------------------------------------------------------
# AI‑powered endpoints
# -------------------------------------------------------------------
@router.post("/ai/symptom_check", response_model=SymptomCheckResponse)
async def symptom_check(
    payload: SymptomCheckRequest, db: Session = Depends(get_db)
) -> SymptomCheckResponse:
    """Validate the pet and forward the request to the DigitalOcean inference service.

    The AI model is expected to return a JSON object with a top‑level ``conditions``
    array. Each element contains ``name``, ``confidence`` and ``urgency`` keys.
    """
    pet = db.get(Pet, payload.pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")

    ai_payload = {
        "pet": {
            "name": pet.name,
            "breed": pet.breed,
            "age_years": pet.age_years,
            "weight_kg": pet.weight_kg,
        },
        "symptom_text": payload.symptom_text,
        "photo_url": payload.photo_url,
    }
    try:
        result = await check_symptoms(ai_payload)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # The model returns a dict with a ``conditions`` key; validate shape quickly.
    conditions = result.get("conditions", [])
    return SymptomCheckResponse(conditions=conditions)


@router.post("/ai/generate_report", response_model=ReportResponse)
async def generate_report_endpoint(
    payload: ReportRequest, db: Session = Depends(get_db)
) -> ReportResponse:
    """Create a health summary report for a pet over a given time window.

    The endpoint aggregates health logs from the database, forwards them to the
    AI model, and returns the generated textual report.
    """
    pet = db.get(Pet, payload.pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")

    logs = (
        db.query(HealthLog)
        .filter(HealthLog.pet_id == payload.pet_id)
        .filter(HealthLog.logged_at >= payload.start_date)
        .filter(HealthLog.logged_at <= payload.end_date)
        .order_by(HealthLog.logged_at)
        .all()
    )

    logs_data = [
        {
            "date": log.logged_at.isoformat(),
            "symptom": log.symptom_text,
            "notes": log.notes,
            "photo_url": log.photo_url,
        }
        for log in logs
    ]

    ai_payload = {
        "pet": {
            "name": pet.name,
            "breed": pet.breed,
            "age_years": pet.age_years,
            "weight_kg": pet.weight_kg,
        },
        "logs": logs_data,
    }

    try:
        result = await generate_report(ai_payload)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    report_text = result.get("report", "")
    return ReportResponse(report_text=report_text)

# Export a router that ``main.py`` can include.
api_router = router
