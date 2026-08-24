from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Delivery, YardDock
from app.schemas import (
    DockAssignmentRequest,
    DockRecommendationResponse,
    DeliveryResponse
)


router = APIRouter(
    prefix="/dock-operations",
    tags=["Dock Operations"]
)


# ============================================================
# DOCK COMPATIBILITY
# ============================================================

def calculate_dock_score(
    delivery: Delivery,
    dock: YardDock
):

    score = 0
    reasons = []

    if dock.status != "available":
        return 0, False, ["Dock is not available"]

    score += 50
    reasons.append("Dock is available")

    # Standard truck compatibility
    if dock.supported_vehicle_type == "truck":
        score += 20
        reasons.append("Vehicle type compatible")

    # Refrigeration
    if dock.refrigerated:
        score += 10
        reasons.append("Refrigerated capability available")

    # General standard dock
    if dock.dock_type == "standard":
        score += 10
        reasons.append("Standard dock suitable for shipment")

    return score, True, reasons


# ============================================================
# RECOMMEND DOCKS
# ============================================================

@router.get(
    "/recommend/{delivery_id}",
    response_model=list[DockRecommendationResponse]
)
def recommend_docks(
    delivery_id: int,
    db: Session = Depends(get_db)
):

    delivery = db.query(Delivery).filter(
        Delivery.id == delivery_id
    ).first()

    if not delivery:
        raise HTTPException(
            status_code=404,
            detail="Delivery not found"
        )

    docks = db.query(YardDock).all()

    recommendations = []

    for dock in docks:

        score, compatible, reasons = calculate_dock_score(
            delivery,
            dock
        )

        recommendations.append(
            DockRecommendationResponse(
                dock_id=dock.id,
                yard_name=dock.yard_name,
                dock_number=dock.dock_number,
                score=score,
                compatible=compatible,
                reasons=reasons
            )
        )

    recommendations.sort(
        key=lambda x: x.score,
        reverse=True
    )

    return recommendations


# ============================================================
# ASSIGN DOCK
# ============================================================

@router.post(
    "/assign/{delivery_id}",
    response_model=DeliveryResponse
)
def assign_dock(
    delivery_id: int,
    request: DockAssignmentRequest,
    db: Session = Depends(get_db)
):

    delivery = db.query(Delivery).filter(
        Delivery.id == delivery_id
    ).first()

    if not delivery:
        raise HTTPException(
            status_code=404,
            detail="Delivery not found"
        )

    dock = db.query(YardDock).filter(
        YardDock.id == request.dock_id
    ).first()

    if not dock:
        raise HTTPException(
            status_code=404,
            detail="Dock not found"
        )

    if dock.status != "available":
        raise HTTPException(
            status_code=400,
            detail="Dock is not available"
        )

    # Release old dock
    if delivery.dock_id is not None:

        old_dock = db.query(YardDock).filter(
            YardDock.id == delivery.dock_id
        ).first()

        if old_dock:
            old_dock.status = "available"

    delivery.dock_id = dock.id

    dock.status = "reserved"

    db.commit()
    db.refresh(delivery)

    return delivery


# ============================================================
# REASSIGN DOCK
# ============================================================

@router.post(
    "/reassign/{delivery_id}",
    response_model=DeliveryResponse
)
def reassign_dock(
    delivery_id: int,
    request: DockAssignmentRequest,
    db: Session = Depends(get_db)
):

    delivery = db.query(Delivery).filter(
        Delivery.id == delivery_id
    ).first()

    if not delivery:
        raise HTTPException(
            status_code=404,
            detail="Delivery not found"
        )

    new_dock = db.query(YardDock).filter(
        YardDock.id == request.dock_id
    ).first()

    if not new_dock:
        raise HTTPException(
            status_code=404,
            detail="New dock not found"
        )

    if new_dock.status != "available":
        raise HTTPException(
            status_code=400,
            detail="New dock is not available"
        )

    # Release old dock
    if delivery.dock_id:

        old_dock = db.query(YardDock).filter(
            YardDock.id == delivery.dock_id
        ).first()

        if old_dock:
            old_dock.status = "available"

    delivery.dock_id = new_dock.id

    new_dock.status = "reserved"

    db.commit()
    db.refresh(delivery)

    return delivery