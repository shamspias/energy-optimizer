from fastapi import APIRouter, HTTPException
from app.models.optimization import OptimizeRequest, OptimizeResponse
from app.services.optimizer import LoadOptimizer
from app.db.storage import storage

router = APIRouter()
optimizer = LoadOptimizer()


@router.post("/optimize/load-shift", response_model=OptimizeResponse)
async def optimize_load_shift(request: OptimizeRequest):
    """Optimize load shifting based on prices"""
    try:
        # Check if we have price data
        prices = storage.get_prices(request.zone_eic, request.date_utc)
        if not prices:
            # Try to fetch if not available
            from app.services.entsoe_client import EntsoeClient
            client = EntsoeClient()
            prices = await client.fetch_day_ahead_prices(request.zone_eic, request.date_utc)
            if prices:
                storage.save_prices(request.zone_eic, request.date_utc, prices)
                optimizer.set_price_data(request.zone_eic, request.date_utc, prices)
            else:
                raise ValueError("No price data available")
        else:
            optimizer.set_price_data(request.zone_eic, request.date_utc, prices)

        # Run optimization
        result = optimizer.optimize(
            zone_eic=request.zone_eic,
            date_str=request.date_utc,
            kwh_flexible=request.kwh_flexible,
            max_shift_hours=request.max_shift_hours,
            objective=request.objective
        )

        # Save run
        storage.save_run({
            'zone_eic': request.zone_eic,
            'date_utc': request.date_utc,
            'kwh_flexible': request.kwh_flexible,
            'savings_eur': result['savings_eur']
        })

        return OptimizeResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
