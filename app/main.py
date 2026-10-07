from fastapi import FastAPI
from app.api.endpoints import router as api_router

app = FastAPI(
    title="Geospatial File Measurement API",
    description="An API to upload geospatial files (Shapefile, KML) and extract measurements.",
    version="1.0.0"
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Geospatial File Measurement API. Go to /docs for Swagger UI."}
