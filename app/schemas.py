from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ============================================================
# SUPPLIER
# ============================================================

class SupplierBase(BaseModel):
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class SupplierCreate(SupplierBase):
    pass


class SupplierResponse(SupplierBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# PRODUCT
# ============================================================

class ProductBase(BaseModel):
    sku: str
    name: str
    category: Optional[str] = None
    unit_price: Optional[float] = None
    reorder_level: int = 0


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# INVENTORY
# ============================================================

class InventoryBase(BaseModel):
    product_id: int
    current_stock: int = 0
    reserved_stock: int = 0


class InventoryCreate(InventoryBase):
    pass


class InventoryResponse(InventoryBase):
    id: int
    last_updated: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# RESTOCK ORDER
# ============================================================

class RestockOrderBase(BaseModel):
    product_id: int
    supplier_id: int
    quantity: int
    status: str = "pending"
    expected_delivery: Optional[datetime] = None


class RestockOrderCreate(RestockOrderBase):
    pass


class RestockOrderResponse(RestockOrderBase):
    id: int
    order_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# YARD DOCK
# ============================================================

class YardDockBase(BaseModel):
    yard_name: str
    dock_number: str
    status: str = "available"


class YardDockCreate(YardDockBase):
    pass


class YardDockResponse(YardDockBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# DELIVERY
# ============================================================

class DeliveryBase(BaseModel):
    restock_order_id: int
    dock_id: Optional[int] = None
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    status: str = "in_transit"
    scheduled_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None


class DeliveryCreate(DeliveryBase):
    pass


class DeliveryResponse(DeliveryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)