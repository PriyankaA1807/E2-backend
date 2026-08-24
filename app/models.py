from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


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


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    category = Column(String(100))
    unit_price = Column(Float)
    reorder_level = Column(Integer, default=0)

    inventory = relationship(
        "Inventory",
        back_populates="product",
        uselist=False
    )

    restock_orders = relationship(
        "RestockOrder",
        back_populates="product"
    )


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
        unique=True
    )
    current_stock = Column(Integer, default=0)
    reserved_stock = Column(Integer, default=0)
    last_updated = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    product = relationship(
        "Product",
        back_populates="inventory"
    )


class RestockOrder(Base):
    __tablename__ = "restock_orders"

    id = Column(Integer, primary_key=True, index=True)
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

    quantity = Column(Integer, nullable=False)
    status = Column(String(50), default="pending")

    order_date = Column(
        DateTime,
        default=datetime.utcnow
    )

    expected_delivery = Column(DateTime)

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


class YardDock(Base):
    __tablename__ = "yard_docks"

    id = Column(Integer, primary_key=True, index=True)
    yard_name = Column(String(100), nullable=False)
    dock_number = Column(String(50), nullable=False)
    status = Column(String(50), default="available")

    deliveries = relationship(
        "Delivery",
        back_populates="dock"
    )


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)

    restock_order_id = Column(
        Integer,
        ForeignKey("restock_orders.id"),
        nullable=False
    )

    dock_id = Column(
        Integer,
        ForeignKey("yard_docks.id")
    )

    tracking_number = Column(String(150), unique=True)
    carrier = Column(String(100))

    status = Column(String(50), default="in_transit")

    scheduled_arrival = Column(DateTime)
    actual_arrival = Column(DateTime)

    restock_order = relationship(
        "RestockOrder",
        back_populates="delivery"
    )

    dock = relationship(
        "YardDock",
        back_populates="deliveries"
    )