from fastapi import APIRouter, HTTPException
from app.models.optimization import AgentAdviseRequest, AgentAdviseResponse, OptimizeRequest
from app.services.agent import EnergyAdvisorAgent
from app.services.optimizer import LoadOptimizer
from app.db.memory import MemoryStore

router = APIRouter()
agent = EnergyAdvisorAgent()
optimizer = LoadOptimizer()
memory = MemoryStore()


@router.post("/agent/advise", response_model=AgentAdviseResponse)
async def get_agent_advice(request: AgentAdviseRequest):
    """Get AI agent advice for load optimization"""
    try:
        # Run optimization first
        opt_result = optimizer.optimize(
            zone_eic=request.zone_eic,
            date_str=request.date_utc,
            kwh_flexible=request.kwh_flexible,
            max_shift_hours=3,
            objective="min_cost"
        )

        # Get agent advice
        advice = await agent.advise(
            user_id=request.user_id,
            optimization_result=opt_result,
            context=request.context,
            zone_eic=request.zone_eic,
            date_str=request.date_utc
        )

        # Save to memory for learning
        if request.context:
            await memory.save_preference(request.user_id, request.context)

        await memory.save_optimization_run(request.user_id, {
            'zone_eic': request.zone_eic,
            'date_utc': request.date_utc,
            'kwh_flexible': request.kwh_flexible,
            'savings_eur': opt_result['savings_eur']
        })

        return AgentAdviseResponse(**advice)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prefs")
async def save_user_preferences(user_id: str, preferences: dict):
    """Save user preferences"""
    try:
        for key, value in preferences.items():
            await memory.save_preference(
                user_id=user_id,
                preference=f"{key}: {value}",
                metadata={"type": "preference"}
            )
        return {"status": "success", "saved": len(preferences)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
