from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import ingest, optimize, agent

app = FastAPI(
    title="ENTSO-E Energy Optimizer",
    description="AI-powered electricity cost optimization using ENTSO-E data",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest.router, tags=["Data Ingestion"])
app.include_router(optimize.router, tags=["Optimization"])
app.include_router(agent.router, tags=["AI Agent"])


@app.get("/")
async def root():
    return {
        "name": "ENTSO-E Energy Optimizer API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "entsoe_configured": bool(settings.entsoe_api_token),
        "ai_configured": bool(settings.openai_api_key),
        "mock_mode": settings.use_mock_data
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
