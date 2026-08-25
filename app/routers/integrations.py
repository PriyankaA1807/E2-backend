from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

from app.database import get_db

from app.models import (
    Product,
    Supplier,
    RestockOrder,
    Delivery,
    ShipmentIntegration
)

from app.schemas import (
    ShipmentIntegrationCreate,
    ShipmentIntegrationResponse
)


router = APIRouter(
    prefix="/integrations",
    tags=["Integrations"]
)


# ============================================================
# PR2 -> E2 SHIPMENT IMPORT
# ============================================================

@router.post(
    "/shipments",
    response_model=ShipmentIntegrationResponse,
    status_code=status.HTTP_201_CREATED
)
def import_shipment(
    shipment: ShipmentIntegrationCreate,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # VALIDATE QUANTITY
    # --------------------------------------------------------

    if shipment.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than zero"
        )

    # --------------------------------------------------------
    # CHECK DUPLICATE EXTERNAL ORDER
    # --------------------------------------------------------

    existing_integration = db.query(
        ShipmentIntegration
    ).filter(
        ShipmentIntegration.external_order_id
        == shipment.external_order_id
    ).first()

    if existing_integration:

        raise HTTPException(
            status_code=409,
            detail={
                "message": (
                    "This external order has already "
                    "been imported into E2"
                ),
                "external_order_id": (
                    shipment.external_order_id
                ),
                "existing_delivery_id": (
                    existing_integration.delivery_id
                )
            }
        )

    # --------------------------------------------------------
    # CHECK DUPLICATE TRACKING NUMBER
    # --------------------------------------------------------

    existing_delivery = db.query(
        Delivery
    ).filter(
        Delivery.tracking_number
        == shipment.tracking_number
    ).first()

    if existing_delivery:

        raise HTTPException(
            status_code=409,
            detail={
                "message": (
                    "Tracking number already exists in E2"
                ),
                "tracking_number": (
                    shipment.tracking_number
                ),
                "existing_delivery_id": (
                    existing_delivery.id
                )
            }
        )

    # --------------------------------------------------------
    # GET OR CREATE GENERIC PR2 PRODUCT
    # --------------------------------------------------------

    product = db.query(
        Product
    ).filter(
        Product.sku == "PR2-INTEGRATION"
    ).first()

    if not product:

        product = Product(
            sku="PR2-INTEGRATION",
            name="PR2 Imported Shipment",
            category="integration",
            unit_price=None,
            reorder_level=0
        )

        db.add(product)
        db.flush()

    # --------------------------------------------------------
    # GET OR CREATE GENERIC PR2 SUPPLIER
    # --------------------------------------------------------

    supplier = db.query(
        Supplier
    ).filter(
        Supplier.name
        == "PR2 Integration Supplier"
    ).first()

    if not supplier:

        supplier = Supplier(
            name="PR2 Integration Supplier",
            contact_person=None,
            email=None,
            phone=None,
            address=None
        )

        db.add(supplier)
        db.flush()

    # --------------------------------------------------------
    # CREATE E2 RESTOCK ORDER
    # --------------------------------------------------------

    restock_order = RestockOrder(
        product_id=product.id,
        supplier_id=supplier.id,
        quantity=shipment.quantity,
        status="pending",
        expected_delivery=shipment.scheduled_arrival
    )

    db.add(restock_order)
    db.flush()

    # --------------------------------------------------------
    # CREATE E2 DELIVERY
    # --------------------------------------------------------

    delivery = Delivery(
        restock_order_id=restock_order.id,

        dock_id=None,

        tracking_number=shipment.tracking_number,

        trailer_id=shipment.trailer_id,

        shipment_reference=(
            shipment.shipment_reference
        ),

        carrier=shipment.carrier,

        status="scheduled",

        scheduled_arrival=(
            shipment.scheduled_arrival
        ),

        actual_arrival=None,

        current_latitude=None,
        current_longitude=None,
        current_location=None,

        destination_latitude=(
            shipment.destination_latitude
        ),

        destination_longitude=(
            shipment.destination_longitude
        ),

        estimated_arrival=None,
        eta_minutes=None,

        average_speed_kmph=50.0,

        distance_remaining_km=None,

        simulation_active=False,

        last_gps_update=None,

        delay_detected=False,
        exception_detected=False
    )

    db.add(delivery)
    db.flush()

    # --------------------------------------------------------
    # CREATE PR2 <-> E2 MAPPING
    # --------------------------------------------------------

    integration = ShipmentIntegration(
        external_order_id=(
            shipment.external_order_id
        ),

        delivery_id=(
            delivery.id
        ),

        source_system=(
            shipment.source_system
        )
    )

    db.add(integration)

    # --------------------------------------------------------
    # COMMIT
    # --------------------------------------------------------

    try:

        db.commit()

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to import shipment into E2"
            )
        )

    db.refresh(
        integration
    )

    db.refresh(
        delivery
    )

    db.refresh(
        restock_order
    )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "message": (
            "Shipment imported successfully into E2"
        ),

        "integration_id": (
            integration.id
        ),

        "delivery_id": (
            delivery.id
        ),

        "restock_order_id": (
            restock_order.id
        ),

        "external_order_id": (
            integration.external_order_id
        ),

        "tracking_number": (
            delivery.tracking_number
        ),

        "trailer_id": (
            delivery.trailer_id
        ),

        "shipment_reference": (
            delivery.shipment_reference
        ),

        "status": (
            delivery.status
        ),

        "source_system": (
            integration.source_system
        )
    }