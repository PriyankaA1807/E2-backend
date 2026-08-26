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


# ============================================================
# WMS ASSIGNED DOCK
# ============================================================

class WMSAssignedDock(BaseModel):
    dock_id: int
    dock_number: str
    yard_name: str
    status: str
    dock_type: str


# ============================================================
# WMS TRAILER
# ============================================================

class WMSTrailerResponse(BaseModel):
    delivery_id: int

    tracking_number: Optional[str] = None
    trailer_id: Optional[str] = None
    shipment_reference: Optional[str] = None

    carrier: Optional[str] = None

    trailer_status: str
    yard_location: Optional[str] = None

    scheduled_arrival: Optional[datetime] = None
    estimated_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None

    eta_minutes: Optional[float] = None

    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None

    distance_remaining_km: Optional[float] = None

    delay_detected: bool = False
    exception_detected: bool = False
    simulation_active: bool = False

    assigned_dock: Optional[WMSAssignedDock] = None


# ============================================================
# WMS DOCK
# ============================================================

class WMSDockResponse(BaseModel):
    dock_id: int

    yard_name: str
    dock_number: str

    status: str
    dock_type: str

    supported_vehicle_type: Optional[str] = None
    max_vehicle_length: Optional[float] = None

    refrigerated: Optional[bool] = None
    hazardous_allowed: Optional[bool] = None


# ============================================================
# WMS SUMMARY
# ============================================================

class WMSSummaryResponse(BaseModel):
    total_trailers: int
    active_shipments: int
    delayed_shipments: int
    waiting_for_dock: int
    total_docks: int
    available_docks: int


# ============================================================
# COMPLETE WMS RESPONSE
# ============================================================

class WMSFeedResponse(BaseModel):
    feed_type: str
    generated_at: datetime

    summary: WMSSummaryResponse

    trailers: list[WMSTrailerResponse]
    docks: list[WMSDockResponse]


# ============================================================
# DOCK SCHEDULE ITEM
# ============================================================

class DockScheduleItem(BaseModel):
    delivery_id: int

    tracking_number: Optional[str] = None
    trailer_id: Optional[str] = None
    shipment_reference: Optional[str] = None

    delivery_status: str
    load_type: str

    priority_score: int

    scheduled_arrival: Optional[datetime] = None
    estimated_arrival: Optional[datetime] = None
    effective_arrival: datetime

    dock_id: int

    yard_name: str
    dock_number: str
    dock_type: str

    window_start: datetime
    window_end: datetime

    score: float

    reasons: list[str]


# ============================================================
# UNSCHEDULED TRAILER
# ============================================================

class UnscheduledTrailer(BaseModel):
    delivery_id: int

    tracking_number: Optional[str] = None
    trailer_id: Optional[str] = None
    shipment_reference: Optional[str] = None

    status: str
    reason: str


# ============================================================
# COMPLETE DOCK SCHEDULE RESPONSE
# ============================================================

class DockScheduleResponse(BaseModel):
    generated_at: datetime

    slot_duration_minutes: int

    total_incoming_trailers: int
    total_docks: int

    scheduled_count: int
    unscheduled_count: int

    schedule: list[DockScheduleItem]

    unscheduled: list[UnscheduledTrailer]


# ============================================================
# DOCK UNAVAILABLE
# ============================================================

class DockUnavailableItem(BaseModel):
    delivery_id: int

    tracking_number: Optional[str] = None
    trailer_id: Optional[str] = None

    dock_id: int
    dock_number: str
    dock_status: str


class DockUnavailableDetectionResponse(BaseModel):
    dock_unavailable: list[DockUnavailableItem]
    count: int


# ============================================================
# DOCK REASSIGNMENT REQUIRED
# ============================================================

class DockReassignmentRequiredItem(BaseModel):
    delivery_id: int

    tracking_number: Optional[str] = None
    trailer_id: Optional[str] = None

    current_dock_id: int
    current_dock_number: str

    dock_status: str

    reassignment_required: bool


class DockReassignmentRequiredResponse(BaseModel):
    reassignment_required: list[
        DockReassignmentRequiredItem
    ]

    count: int


# ============================================================
# ETA INPUT
# ============================================================

class ETAInputResponse(BaseModel):
    distance_km: float
    quantity: float

    supplier_delay_history: float
    carrier_delay_history: float


# ============================================================
# ETA PREDICTION
# ============================================================

class ETAPredictionDetails(BaseModel):
    estimated_delivery_hours: float
    estimated_delivery_minutes: float
    estimated_arrival: datetime


# ============================================================
# ETA SCHEDULE
# ============================================================

class ETAScheduleDetails(BaseModel):
    scheduled_arrival: Optional[datetime] = None

    predicted_delay_minutes: float
    delay_threshold_minutes: float


# ============================================================
# ETA DELAY
# ============================================================

class ETADelayDetails(BaseModel):
    delay_detected: bool
    alert_created: bool
    current_status: str


# ============================================================
# DELIVERY ETA RESPONSE
# ============================================================

class DeliveryETAPredictionResponse(BaseModel):
    delivery_id: int

    tracking_number: Optional[str] = None
    trailer_id: Optional[str] = None

    model: str

    inputs: ETAInputResponse
    prediction: ETAPredictionDetails
    schedule: ETAScheduleDetails
    delay: ETADelayDetails

    evaluated_at: datetime


# ============================================================
# YARD STATUS - ASSIGNED DOCK
# ============================================================

class YardAssignedDockResponse(BaseModel):
    dock_id: int

    yard_name: str
    dock_number: str

    dock_status: str
    dock_type: str


# ============================================================
# YARD STATUS - TRAILER
# ============================================================

class YardTrailerStatusResponse(BaseModel):
    delivery_id: int

    tracking_number: Optional[str] = None
    trailer_id: Optional[str] = None
    shipment_reference: Optional[str] = None

    carrier: Optional[str] = None

    status: str
    operational_state: str

    yard_location: Optional[str] = None

    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None

    scheduled_arrival: Optional[datetime] = None
    estimated_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None

    eta_minutes: Optional[float] = None
    distance_remaining_km: Optional[float] = None

    delay_detected: bool
    exception_detected: bool

    assigned_dock: Optional[
        YardAssignedDockResponse
    ] = None


# ============================================================
# YARD STATUS SUMMARY
# ============================================================

class YardStatusSummaryResponse(BaseModel):
    total_active_trailers: int

    at_gate: int
    in_yard: int
    waiting_for_dock: int

    dock_assigned: int
    docked_or_unloading: int

    delayed: int


class YardStatusResponse(BaseModel):
    summary: YardStatusSummaryResponse

    trailers: list[
        YardTrailerStatusResponse
    ]



class TrailerCurrentDoorResponse(BaseModel):
    dock_id: int

    yard_name: str
    dock_number: str

    dock_status: str
    dock_type: str




class TrailerScheduledDoorResponse(BaseModel):
    dock_id: int

    yard_name: str
    dock_number: str
    dock_type: str

    window_start: datetime
    window_end: datetime

    score: float

    reasons: list[str]



class TrailerDoorAllocationItem(BaseModel):
    delivery_id: int

    tracking_number: Optional[str] = None
    trailer_id: Optional[str] = None
    shipment_reference: Optional[str] = None

    carrier: Optional[str] = None

    delivery_status: str

    scheduled_arrival: Optional[datetime] = None
    estimated_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None

    eta_minutes: Optional[float] = None

    delay_detected: bool
    exception_detected: bool

    current_dock: Optional[
        TrailerCurrentDoorResponse
    ] = None

    scheduled_dock: Optional[
        TrailerScheduledDoorResponse
    ] = None

    reassignment_required: bool

    allocation_status: str




class TrailerDoorAllocationSummary(BaseModel):
    total_trailers: int

    currently_assigned: int
    assignment_recommended: int

    reassignment_required: int
    unscheduled: int

    delayed: int




class TrailerDoorAllocationResponse(BaseModel):
    generated_at: datetime

    summary: TrailerDoorAllocationSummary

    allocations: list[
        TrailerDoorAllocationItem
    ]

    # ============================================================
# PR2 -> E2 SHIPMENT INTEGRATION
# ============================================================

class ShipmentIntegrationCreate(BaseModel):
    external_order_id: str

    tracking_number: str
    trailer_id: Optional[str] = None
    shipment_reference: Optional[str] = None

    carrier: Optional[str] = None

    quantity: int

    scheduled_arrival: Optional[datetime] = None

    destination_latitude: Optional[float] = None
    destination_longitude: Optional[float] = None

    source_system: str = "PR2"


class ShipmentIntegrationResponse(BaseModel):
    message: str

    integration_id: int
    delivery_id: int
    restock_order_id: int

    external_order_id: str
    tracking_number: str

    trailer_id: Optional[str] = None
    shipment_reference: Optional[str] = None

    status: str
    source_system: str

# ============================================================
# PR2 -> E2 SHIPMENT INTEGRATION
# ============================================================

class ShipmentIntegrationCreate(BaseModel):
    external_order_id: str

    tracking_number: str
    trailer_id: Optional[str] = None
    shipment_reference: Optional[str] = None

    carrier: Optional[str] = None

    quantity: int

    scheduled_arrival: Optional[datetime] = None

    destination_latitude: Optional[float] = None
    destination_longitude: Optional[float] = None

    source_system: str = "PR2"


class ShipmentIntegrationResponse(BaseModel):
    message: str

    integration_id: int
    delivery_id: int
    restock_order_id: int

    external_order_id: str
    tracking_number: str

    trailer_id: Optional[str] = None
    shipment_reference: Optional[str] = None

    status: str
    source_system: str

# ============================================================
# GPS SIMULATION RESPONSES
# ============================================================

class SimulationStartResponse(BaseModel):
    message: str
    delivery_id: int

    tracking_number: Optional[str] = None
    trailer_id: Optional[str] = None

    status: str
    simulation_active: bool

    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    current_location: Optional[str] = None

    distance_remaining_km: Optional[float] = None
    eta_minutes: Optional[float] = None

    estimated_arrival: Optional[datetime] = None


class SimulationStepResponse(BaseModel):
    message: str
    delivery_id: int

    tracking_number: Optional[str] = None
    trailer_id: Optional[str] = None

    status: str

    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    current_location: Optional[str] = None

    average_speed_kmph: Optional[float] = None

    distance_remaining_km: Optional[float] = None
    eta_minutes: Optional[float] = None

    estimated_arrival: Optional[datetime] = None

    simulation_active: bool


class SimulationStopResponse(BaseModel):
    message: str
    delivery_id: int
    status: str
    simulation_active: bool

