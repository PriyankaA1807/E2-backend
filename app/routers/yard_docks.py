from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import YardDock
from app.schemas import (
    YardDockCreate,
    YardDockResponse
)


router = APIRouter(
    prefix="/yard-docks",
    tags=["Yard & Docks"]
)


# ============================================================
# CREATE DOCK
# ============================================================

@router.post(
    "/",
    response_model=YardDockResponse,
    status_code=201
)
def create_yard_dock(
    dock_data: YardDockCreate,
    db: Session = Depends(get_db)
):

    dock = YardDock(
        yard_name=dock_data.yard_name,
        dock_number=dock_data.dock_number,
        status=dock_data.status,
        dock_type=dock_data.dock_type,
        supported_vehicle_type=dock_data.supported_vehicle_type,
        max_vehicle_length=dock_data.max_vehicle_length,
        refrigerated=dock_data.refrigerated,
        hazardous_allowed=dock_data.hazardous_allowed
    )

    db.add(dock)
    db.commit()
    db.refresh(dock)

    return dock


# ============================================================
# GET ALL DOCKS
# ============================================================

@router.get(
    "/",
    response_model=list[YardDockResponse]
)
def get_yard_docks(
    db: Session = Depends(get_db)
):

    return db.query(YardDock).all()


# ============================================================
# GET ONE DOCK
# ============================================================

@router.get(
    "/{dock_id}",
    response_model=YardDockResponse
)
def get_yard_dock(
    dock_id: int,
    db: Session = Depends(get_db)
):

    dock = db.query(YardDock).filter(
        YardDock.id == dock_id
    ).first()

    if not dock:
        raise HTTPException(
            status_code=404,
            detail="Yard/Dock not found"
        )

    return dock


# ============================================================
# UPDATE DOCK STATUS
# ============================================================

@router.put(
    "/{dock_id}",
    response_model=YardDockResponse
)
def update_yard_dock(
    dock_id: int,
    status: str,
    db: Session = Depends(get_db)
):

    dock = db.query(YardDock).filter(
        YardDock.id == dock_id
    ).first()

    if not dock:
        raise HTTPException(
            status_code=404,
            detail="Yard/Dock not found"
        )

    allowed = {
        "available",
        "occupied",
        "reserved",
        "maintenance",
        "blocked"
    }

    status = status.lower().strip()

    if status not in allowed:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid dock status",
                "allowed_statuses": sorted(allowed)
            }
        )

    dock.status = status

    db.commit()
    db.refresh(dock)

    return dock


# ============================================================
# DELETE DOCK
# ============================================================

@router.delete("/{dock_id}")
def delete_yard_dock(
    dock_id: int,
    db: Session = Depends(get_db)
):

    dock = db.query(YardDock).filter(
        YardDock.id == dock_id
    ).first()

    if not dock:
        raise HTTPException(
            status_code=404,
            detail="Yard/Dock not found"
        )

    if dock.status == "occupied":
        raise HTTPException(
            status_code=400,
            detail="Cannot delete an occupied dock"
        )

    db.delete(dock)
    db.commit()

    return {
        "message": "Yard/Dock deleted successfully"
    }