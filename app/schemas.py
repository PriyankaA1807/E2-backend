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
# YARD / DOCK
# ============================================================

class YardDockBase(BaseModel):
    yard_name: str
    dock_number: str
    status: str = "available"

    dock_type: str = "standard"
    supported_vehicle_type: str = "truck"
    max_vehicle_length: float = 20.0
    refrigerated: bool = False
    hazardous_allowed: bool = False


class YardDockCreate(YardDockBase):
    pass


class YardDockResponse(YardDockBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# DELIVERY / SHIPMENT
# ============================================================

class DeliveryBase(BaseModel):

    restock_order_id: int

    dock_id: Optional[int] = None

    tracking_number: Optional[str] = None

    trailer_id: Optional[str] = None

    shipment_reference: Optional[str] = None

    carrier: Optional[str] = None

    status: str = "scheduled"

    scheduled_arrival: Optional[datetime] = None

    actual_arrival: Optional[datetime] = None

    current_latitude: Optional[float] = None

    current_longitude: Optional[float] = None

    current_location: Optional[str] = None

    destination_latitude: Optional[float] = None

    destination_longitude: Optional[float] = None

    estimated_arrival: Optional[datetime] = None

    eta_minutes: Optional[float] = None

    average_speed_kmph: Optional[float] = 50.0

    distance_remaining_km: Optional[float] = None

    simulation_active: bool = False


class DeliveryCreate(DeliveryBase):
    pass


class DeliveryResponse(DeliveryBase):
    id: int

    delay_detected: bool = False

    exception_detected: bool = False

    last_gps_update: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# TRACKING EVENT
# ============================================================

class TrackingEventCreate(BaseModel):
    status: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    event_time: Optional[datetime] = None
    description: Optional[str] = None


class TrackingEventResponse(TrackingEventCreate):
    id: int
    delivery_id: int
    event_time: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# DOCK ASSIGNMENT
# ============================================================

class DockAssignmentRequest(BaseModel):
    dock_id: int


class DockRecommendationResponse(BaseModel):
    dock_id: int
    yard_name: str
    dock_number: str
    score: float
    compatible: bool
    reasons: list[str]


# ============================================================
# ALERT
# ============================================================

class AlertResponse(BaseModel):
    id: int
    delivery_id: Optional[int] = None
    alert_type: str
    severity: str
    title: str
    message: str
    resolved: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)