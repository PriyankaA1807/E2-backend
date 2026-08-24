from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import YardDock


router = APIRouter(
    prefix="/yard-docks",
    tags=["Yard & Docks"]
)


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create Yard/Dock
@router.post("/")
def create_yard_dock(
    yard_name: str,
    dock_number: str,
    status: str = "available",
    db: Session = Depends(get_db)
):
    dock = YardDock(
        yard_name=yard_name,
        dock_number=dock_number,
        status=status
    )

    db.add(dock)
    db.commit()
    db.refresh(dock)

    return dock


# Get all Yard/Docks
@router.get("/")
def get_yard_docks(
    db: Session = Depends(get_db)
):
    docks = db.query(YardDock).all()

    return docks


# Get one Yard/Dock
@router.get("/{dock_id}")
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


# Update Yard/Dock
@router.put("/{dock_id}")
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

    dock.status = status

    db.commit()
    db.refresh(dock)

    return dock


# Delete Yard/Dock
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

    db.delete(dock)
    db.commit()

    return {
        "message": "Yard/Dock deleted successfully"
    }