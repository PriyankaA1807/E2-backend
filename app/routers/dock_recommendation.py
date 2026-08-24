from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from app.ml.dock_recommender import recommend_dock


router = APIRouter(
    prefix="/dock-recommendation",
    tags=["Dock Recommendation"]
)


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class DockInput(BaseModel):
    id: int
    dock_number: str
    yard_name: str
    status: str = "available"
    dock_type: str = "general"
    available_in_hours: float = 0


class DockRecommendationRequest(BaseModel):
    docks: List[DockInput]
    truck_eta_hours: float
    priority: str = "normal"
    load_type: str = "general"


# ============================================================
# RESPONSE SCHEMAS
# ============================================================

class RecommendedDock(BaseModel):
    dock_id: int
    dock_number: str
    yard_name: str
    score: float
    reasons: List[str]


class DockRecommendationResponse(BaseModel):
    recommended_dock: RecommendedDock
    score: float
    reason: str
    alternatives: List[RecommendedDock]


# ============================================================
# DOCK RECOMMENDATION
# ============================================================

@router.post(
    "/",
    response_model=DockRecommendationResponse
)
def get_dock_recommendation(
    request: DockRecommendationRequest
):

    docks = [
        dock.model_dump()
        for dock in request.docks
    ]

    result = recommend_dock(
        docks=docks,
        truck_eta_hours=request.truck_eta_hours,
        priority=request.priority,
        load_type=request.load_type
    )

    return result