from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from models import get_session, Pet, HealthLog
from ai_service import check_symptoms, generate_report

router = APIRouter()


def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


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


@router.post("/ai/symptom_check", response_model=SymptomCheckResponse)
async def symptom_check(
    payload: SymptomCheckRequest, db: Session = Depends(get_db)
) -> SymptomCheckResponse:
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

    conditions = result.get("conditions", [])
    return SymptomCheckResponse(conditions=conditions)


@router.post("/ai/generate_report", response_model=ReportResponse)
async def generate_report_endpoint(
    payload: ReportRequest, db: Session = Depends(get_db)
) -> ReportResponse:
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


api_router = router
