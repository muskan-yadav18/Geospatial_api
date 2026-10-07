from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class FileInfoResponse(BaseModel):
    id: str
    filename: str
    feature_count: int
    crs: Optional[str]
    status: str

class FeatureMeasurement(BaseModel):
    feature_id: int
    geometry_type: str
    properties: Dict[str, Any]
    crs: str
    measurement_type: Optional[str] = None
    measurement_value: Optional[float] = None
    unit: Optional[str] = None

class MeasurementsResponse(BaseModel):
    id: str
    measurements: List[FeatureMeasurement]
