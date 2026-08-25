from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine

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
    dashboard,
    dock_recommendation,
    integrations,
)

from app.background import tracking_background_loop


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# APPLICATION LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    # Start background shipment tracking
    background_task = asyncio.create_task(
        tracking_background_loop()
    )

    print("E2 background tracking started")

    yield

    # Stop background task during shutdown
    background_task.cancel()

    try:
        await background_task

    except asyncio.CancelledError:
        pass

    print("E2 background tracking stopped")


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="E2 Smart Restock & Yard Dock Delivery Tracker",
    description=(
        "Backend API for smart restocking, shipment tracking, "
        "ETA prediction, GPS simulation, yard and dock "
        "management, operational alerts, dashboard monitoring, "
        "dock scheduling, and PR2 shipment integration."
    ),
    version="2.0.0",
    lifespan=lifespan,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    # Development setting.
    # Later, after frontend deployment, replace "*" with the
    # frontend URL.
    allow_origins=["*"],

    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(
    products.router
)

app.include_router(
    inventory.router
)

app.include_router(
    suppliers.router
)

app.include_router(
    restock_orders.router
)

app.include_router(
    yard_docks.router
)

app.include_router(
    deliveries.router
)

app.include_router(
    eta.router
)

app.include_router(
    tracking.router
)

app.include_router(
    dock_operations.router
)

app.include_router(
    simulation.router
)

app.include_router(
    operations.router
)

app.include_router(
    dashboard.router
)

app.include_router(
    dock_recommendation.router
)

# ============================================================
# PR2 -> E2 INTEGRATION ROUTER
# ============================================================

app.include_router(
    integrations.router
)


# ============================================================
# ROOT
# ============================================================

@app.get(
    "/",
    tags=["System"]
)
def root():

    return {
        "message": "E2 Backend is running",
        "version": "2.0.0"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get(
    "/health",
    tags=["System"]
)
def health_check():

    return {
        "status": "healthy",
        "service": "E2 Backend",
        "version": "2.0.0"
    }