from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="ClairDiag",
    description="Demo: симптоми → діагнози → аналізи",
    version="0.1.0",
)

app.include_router(router, prefix="/v1")


@app.get("/", include_in_schema=False)
def root():
    return {"service": "ClairDiag", "docs": "/docs"}
