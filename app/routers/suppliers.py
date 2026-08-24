from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Supplier


router = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"]
)


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# GET all suppliers
@router.get("/")
def get_suppliers(db: Session = Depends(get_db)):
    suppliers = db.query(Supplier).all()
    return suppliers


# GET supplier by ID
@router.get("/{supplier_id}")
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db)
):
    supplier = (
        db.query(Supplier)
        .filter(Supplier.id == supplier_id)
        .first()
    )

    if not supplier:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found"
        )

    return supplier


# POST create supplier
@router.post("/")
def create_supplier(
    name: str,
    contact_person: str = None,
    email: str = None,
    phone: str = None,
    address: str = None,
    db: Session = Depends(get_db)
):
    supplier = Supplier(
        name=name,
        contact_person=contact_person,
        email=email,
        phone=phone,
        address=address
    )

    db.add(supplier)
    db.commit()
    db.refresh(supplier)

    return supplier


# PUT update supplier
@router.put("/{supplier_id}")
def update_supplier(
    supplier_id: int,
    name: str,
    contact_person: str = None,
    email: str = None,
    phone: str = None,
    address: str = None,
    db: Session = Depends(get_db)
):
    supplier = (
        db.query(Supplier)
        .filter(Supplier.id == supplier_id)
        .first()
    )

    if not supplier:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found"
        )

    supplier.name = name
    supplier.contact_person = contact_person
    supplier.email = email
    supplier.phone = phone
    supplier.address = address

    db.commit()
    db.refresh(supplier)

    return supplier


# DELETE supplier
@router.delete("/{supplier_id}")
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db)
):
    supplier = (
        db.query(Supplier)
        .filter(Supplier.id == supplier_id)
        .first()
    )

    if not supplier:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found"
        )

    db.delete(supplier)
    db.commit()

    return {
        "message": "Supplier deleted successfully"
    }