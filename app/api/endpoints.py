import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import FileInfoResponse, MeasurementsResponse
from app.services import geospatial

router = APIRouter()

@router.post("/files/", response_model=FileInfoResponse)
async def upload_file(file: UploadFile = File(...)):
    if not (file.filename.endswith('.zip') or file.filename.endswith('.kml')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .zip (Shapefile) or .kml are supported.")
        
    file_location = os.path.join(geospatial.UPLOAD_DIR, file.filename)
    
    # Save the file temporarily
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
        
    try:
        file_id = geospatial.process_file(file_location, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        # Cleanup file after reading into memory
        if os.path.exists(file_location):
            os.remove(file_location)
            
    info = geospatial.get_file_info(file_id)
    return info

@router.get("/files/{file_id}/", response_model=FileInfoResponse)
async def get_file_info(file_id: str):
    info = geospatial.get_file_info(file_id)
    if not info:
        raise HTTPException(status_code=404, detail="File not found")
    return info

@router.get("/files/{file_id}/measurements/", response_model=MeasurementsResponse)
async def get_file_measurements(file_id: str):
    measurements = geospatial.get_measurements(file_id)
    if measurements is None:
        raise HTTPException(status_code=404, detail="File not found")
        
    return {"id": file_id, "measurements": measurements}
