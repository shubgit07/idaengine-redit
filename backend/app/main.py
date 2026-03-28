from fastapi import FastAPI

from app.api.pain_points import router as pain_points_router

app = FastAPI(title="Opportunity Engine")
app.include_router(pain_points_router, prefix="/pain-points", tags=["Pain Points"])


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "ok"}
