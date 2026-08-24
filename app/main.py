import asyncio

from fastapi import FastAPI
from sqlalchemy import text

from app.database import engine, Base
from app.background import tracking_background_loop

from app.routers import (
    products,
    inventory,
    suppliers,
    restock_orders,
    yard_docks,
    deliveries,
    eta,
    tracking,
    dock_operations,
    simulation,
    operations,
    dashboard
)


app = FastAPI(
    title="E2 - Smart Restock & Yard Dock Delivery Tracker",
    version="2.0.0",
    description=(
        "Smart restocking, shipment tracking, "
        "GPS simulation, ETA prediction, yard/dock "
        "management, alerts and operational insights."
    )
)


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
async def startup():

    # Create database tables
    Base.metadata.create_all(
        bind=engine
    )

    # Start automatic background GPS tracking
    app.state.tracking_task = asyncio.create_task(
        tracking_background_loop()
    )


# ============================================================
# SHUTDOWN
# ============================================================

@app.on_event("shutdown")
async def shutdown():

    tracking_task = getattr(
        app.state,
        "tracking_task",
        None
    )

    if tracking_task:

        tracking_task.cancel()

        try:
            await tracking_task

        except asyncio.CancelledError:
            pass


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "message": "E2 Backend is running",
        "version": "2.0.0"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health_check():

    try:

        with engine.connect() as connection:

            connection.execute(
                text("SELECT 1")
            )

        return {
            "status": "healthy",
            "database": "connected"
        }

    except Exception as e:

        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


# ============================================================
# API STATUS
# ============================================================

@app.get("/api/status")
def api_status():

    return {
        "status": "online",
        "service": "E2 Backend",
        "version": "2.0.0",
        "features": [
            "shipment_tracking",
            "gps_simulation",
            "real_time_eta",
            "yard_management",
            "dock_compatibility",
            "dock_recommendation",
            "dock_assignment",
            "dock_reassignment",
            "delay_detection",
            "exception_detection",
            "alerts",
            "operational_insights",
            "dashboard"
        ]
    }


# ============================================================
# PRODUCTS
# ============================================================

app.include_router(
    products.router
)


# ============================================================
# INVENTORY
# ============================================================

app.include_router(
    inventory.router
)


# ============================================================
# SUPPLIERS
# ============================================================

app.include_router(
    suppliers.router
)


# ============================================================
# RESTOCK ORDERS
# ============================================================

app.include_router(
    restock_orders.router
)


# ============================================================
# YARD DOCKS
# ============================================================

app.include_router(
    yard_docks.router
)


# ============================================================
# DELIVERIES
# ============================================================

app.include_router(
    deliveries.router
)


# ============================================================
# ETA
# ============================================================

app.include_router(
    eta.router
)


# ============================================================
# TRACKING
# ============================================================

app.include_router(
    tracking.router
)


# ============================================================
# DOCK OPERATIONS
# ============================================================

app.include_router(
    dock_operations.router
)


# ============================================================
# GPS SIMULATION
# ============================================================

app.include_router(
    simulation.router
)


# ============================================================
# OPERATIONS / ALERTS
# ============================================================

app.include_router(
    operations.router
)


# ============================================================
# DASHBOARD
# ============================================================

app.include_router(
    dashboard.router
)