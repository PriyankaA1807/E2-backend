from fastapi import APIRouter, HTTPException
from app.ml.eta import predict_eta

router = APIRouter(
    prefix="/eta",
    tags=["ETA"]
)


@router.get("/predict")
def get_eta(
    distance_km: float,
    quantity: float,
    supplier_delay_history: float,
    carrier_delay_history: float
):
    try:
        result = predict_eta(
            distance_km=distance_km,
            quantity=quantity,
            supplier_delay_history=supplier_delay_history,
            carrier_delay_history=carrier_delay_history
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )