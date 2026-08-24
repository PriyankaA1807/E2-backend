from fastapi import FastAPI
from sqlalchemy import text

from app.database import engine, Base
from app.routers import products, inventory, suppliers, restock_orders, yard_docks, deliveries, eta

app = FastAPI(
    title="E2 - Smart Restock & Yard Dock Delivery Tracker",
    version="1.0.0",
    description="Backend API for smart restocking and yard/dock delivery tracking."
)


@app.get("/")
def root():
    return {
        "message": "E2 Backend is running"
    }


@app.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

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


@app.get("/api/status")
def api_status():
    return {
        "status": "online",
        "service": "E2 Backend",
        "version": "1.0.0"
    }


app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(suppliers.router)
app.include_router(restock_orders.router)
app.include_router(yard_docks.router)
app.include_router(deliveries.router)
app.include_router(eta.router)