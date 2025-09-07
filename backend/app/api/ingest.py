from fastapi import APIRouter, HTTPException
from app.models.entsoe import EntsoeIngestRequest, EntsoeIngestResponse
from app.services.entsoe_client import EntsoeClient
from app.services.optimizer import LoadOptimizer
from app.db.storage import storage

router = APIRouter()
entsoe_client = EntsoeClient()
optimizer = LoadOptimizer()


@router.post("/ingest/entsoe", response_model=EntsoeIngestResponse)
async def ingest_entsoe_data(request: EntsoeIngestRequest):
    """Fetch and store ENTSO-E data"""
    try:
        response_data = {
            "zone_eic": request.zone_eic,
            "hours": 0,
            "has_prices": False,
            "has_load": False,
            "data": {}
        }

        # Fetch day-ahead prices
        if "day_ahead_prices" in request.fetch:
            prices = await entsoe_client.fetch_day_ahead_prices(
                request.zone_eic,
                request.date_utc
            )
            if prices:
                storage.save_prices(request.zone_eic, request.date_utc, prices)
                optimizer.set_price_data(request.zone_eic, request.date_utc, prices)
                response_data["has_prices"] = True
                response_data["hours"] = len(prices)
                response_data["data"]["prices"] = prices

        # Fetch actual load
        if "actual_load" in request.fetch:
            loads = await entsoe_client.fetch_actual_load(
                request.zone_eic,
                request.date_utc
            )
            if loads:
                storage.save_load(request.zone_eic, request.date_utc, loads)
                response_data["has_load"] = True
                response_data["data"]["loads"] = loads

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
