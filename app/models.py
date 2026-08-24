from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


# ============================================================
# SUPPLIER
# ============================================================

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    contact_person = Column(String(100))
    email = Column(String(150))
    phone = Column(String(30))
    address = Column(Text)

    restock_orders = relationship(
        "RestockOrder",
        back_populates="supplier"
    )


# ============================================================
# PRODUCT
# ============================================================

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    sku = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    name = Column(
        String(150),
        nullable=False
    )

    category = Column(String(100))

    unit_price = Column(Float)

    reorder_level = Column(
        Integer,
        default=0
    )

    inventory = relationship(
        "Inventory",
        back_populates="product",
        uselist=False
    )

    restock_orders = relationship(
        "RestockOrder",
        back_populates="product"
    )


# ============================================================
# INVENTORY
# ============================================================

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
        unique=True
    )

    current_stock = Column(
        Integer,
        default=0
    )

    reserved_stock = Column(
        Integer,
        default=0
    )

    last_updated = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    product = relationship(
        "Product",
        back_populates="inventory"
    )


# ============================================================
# RESTOCK ORDER
# ============================================================

class RestockOrder(Base):
    __tablename__ = "restock_orders"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    supplier_id = Column(
        Integer,
        ForeignKey("suppliers.id"),
        nullable=False
    )

    quantity = Column(
        Integer,
        nullable=False
    )

    status = Column(
        String(50),
        default="pending"
    )

    order_date = Column(
        DateTime,
        default=datetime.utcnow
    )

    expected_delivery = Column(
        DateTime
    )

    product = relationship(
        "Product",
        back_populates="restock_orders"
    )

    supplier = relationship(
        "Supplier",
        back_populates="restock_orders"
    )

    delivery = relationship(
        "Delivery",
        back_populates="restock_order",
        uselist=False
    )


# ============================================================
# YARD / DOCK
# ============================================================

class YardDock(Base):
    __tablename__ = "yard_docks"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    yard_name = Column(
        String(100),
        nullable=False
    )

    dock_number = Column(
        String(50),
        nullable=False
    )

    status = Column(
        String(50),
        default="available"
    )

    # Dock compatibility
    dock_type = Column(
        String(50),
        default="standard"
    )

    supported_vehicle_type = Column(
        String(50),
        default="truck"
    )

    max_vehicle_length = Column(
        Float,
        default=20.0
    )

    refrigerated = Column(
        Boolean,
        default=False
    )

    hazardous_allowed = Column(
        Boolean,
        default=False
    )

    deliveries = relationship(
        "Delivery",
        back_populates="dock"
    )


# ============================================================
# DELIVERY / SHIPMENT
# ============================================================

class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    restock_order_id = Column(
        Integer,
        ForeignKey("restock_orders.id"),
        nullable=False
    )

    dock_id = Column(
        Integer,
        ForeignKey("yard_docks.id"),
        nullable=True
    )

    # Shipment identification
    tracking_number = Column(
        String(150),
        unique=True,
        index=True
    )

    trailer_id = Column(
        String(100),
        index=True
    )

    shipment_reference = Column(
        String(150),
        index=True
    )

    carrier = Column(
        String(100)
    )

    # Delivery status
    status = Column(
        String(50),
        default="scheduled"
    )

    # Arrival information
    scheduled_arrival = Column(
        DateTime
    )

    actual_arrival = Column(
        DateTime
    )

    # ========================================================
    # GPS / MOVEMENT
    # ========================================================

    current_latitude = Column(
        Float
    )

    current_longitude = Column(
        Float
    )

    current_location = Column(
        String(255)
    )

    destination_latitude = Column(
        Float
    )

    destination_longitude = Column(
        Float
    )

    # Estimated arrival
    estimated_arrival = Column(
        DateTime
    )

    eta_minutes = Column(
        Float
    )

    average_speed_kmph = Column(
        Float,
        default=50.0
    )

    distance_remaining_km = Column(
        Float
    )

    # Simulation
    simulation_active = Column(
        Boolean,
        default=False
    )

    last_gps_update = Column(
        DateTime
    )

    # Operational flags
    delay_detected = Column(
        Boolean,
        default=False
    )

    exception_detected = Column(
        Boolean,
        default=False
    )

    restock_order = relationship(
        "RestockOrder",
        back_populates="delivery"
    )

    dock = relationship(
        "YardDock",
        back_populates="deliveries"
    )

    tracking_events = relationship(
        "TrackingEvent",
        back_populates="delivery",
        cascade="all, delete-orphan",
        order_by="TrackingEvent.event_time"
    )

    alerts = relationship(
        "Alert",
        back_populates="delivery",
        cascade="all, delete-orphan"
    )


# ============================================================
# TRACKING EVENTS
# ============================================================

class TrackingEvent(Base):
    __tablename__ = "tracking_events"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    delivery_id = Column(
        Integer,
        ForeignKey("deliveries.id"),
        nullable=False,
        index=True
    )

    status = Column(
        String(50),
        nullable=False
    )

    location = Column(
        String(255)
    )

    latitude = Column(
        Float
    )

    longitude = Column(
        Float
    )

    event_time = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    description = Column(
        Text
    )

    delivery = relationship(
        "Delivery",
        back_populates="tracking_events"
    )


# ============================================================
# ALERTS
# ============================================================

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    delivery_id = Column(
        Integer,
        ForeignKey("deliveries.id"),
        nullable=True
    )

    alert_type = Column(
        String(100),
        nullable=False
    )

    severity = Column(
        String(50),
        default="medium"
    )

    title = Column(
        String(200),
        nullable=False
    )

    message = Column(
        Text,
        nullable=False
    )

    resolved = Column(
        Boolean,
        default=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    delivery = relationship(
        "Delivery",
        back_populates="alerts"
    )