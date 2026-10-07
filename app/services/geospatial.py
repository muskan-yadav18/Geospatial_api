import os
import uuid
import geopandas as gpd
import fiona
from typing import Dict, Any, List

# Enable KML driver
fiona.drvsupport.supported_drivers['KML'] = 'rw'

UPLOAD_DIR = os.path.join(os.getcwd(), 'data')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory storage for file metadata and DataFrames
# In a real app, this would be a database and a blob storage (S3) or similar.
file_storage: Dict[str, Dict[str, Any]] = {}
dataframes: Dict[str, gpd.GeoDataFrame] = {}

def process_file(file_path: str, filename: str) -> str:
    file_id = str(uuid.uuid4())
    
    try:
        if filename.endswith('.kml'):
            gdf = gpd.read_file(file_path, driver='KML')
        elif filename.endswith('.zip'):
            # geopandas can read shapefiles directly from zip
            gdf = gpd.read_file(f"zip://{file_path}")
        else:
            raise ValueError("Unsupported file format. Please upload a .kml or a .zip containing a shapefile.")
        
        # Store metadata
        file_storage[file_id] = {
            "id": file_id,
            "filename": filename,
            "feature_count": len(gdf),
            "crs": str(gdf.crs) if gdf.crs else None,
            "status": "COMPLETED"
        }
        
        # Store the dataframe
        dataframes[file_id] = gdf
        return file_id
        
    except Exception as e:
        # In a real app, log the exception and perhaps save a FAILED state
        print(f"Error processing file: {e}")
        raise ValueError(f"Failed to process file: {str(e)}")

def get_file_info(file_id: str) -> Dict[str, Any]:
    if file_id not in file_storage:
        return None
    return file_storage[file_id]

def get_measurements(file_id: str) -> List[Dict[str, Any]]:
    if file_id not in dataframes:
        return None
        
    gdf = dataframes[file_id]
    measurements = []
    
    # Check if the CRS is geographic. If so, project it to an appropriate UTM zone
    # to calculate accurate measurements (meters).
    if gdf.crs and gdf.crs.is_geographic:
        # estimate_utm_crs is available in geopandas >= 0.9 and automatically finds the right UTM zone
        projected_gdf = gdf.to_crs(gdf.estimate_utm_crs())
    else:
        projected_gdf = gdf
        
    # Get the original CRS string to include in the output as requested
    original_crs = str(gdf.crs) if gdf.crs else "Unknown"

    for idx, row in projected_gdf.iterrows():
        geom = row.geometry
        if geom is None:
            continue
            
        geom_type = geom.geom_type
        props = row.drop('geometry').to_dict()
        
        measurement_info = {
            "feature_id": idx,
            "geometry_type": geom_type,
            "properties": props,
            "crs": original_crs
        }
        
        try:
            if geom_type in ['Polygon', 'MultiPolygon']:
                measurement_info["measurement_type"] = "Area"
                measurement_info["measurement_value"] = geom.area
                measurement_info["unit"] = "Square Meters"
            elif geom_type in ['LineString', 'MultiLineString']:
                measurement_info["measurement_type"] = "Length"
                measurement_info["measurement_value"] = geom.length
                measurement_info["unit"] = "Meters"
            elif geom_type in ['Point', 'MultiPoint']:
                # No measurement required for point
                pass
            else:
                # Handle unknown geometries gracefully without crashing
                pass
        except Exception:
            # Gracefully handle any calculation errors
            pass
            
        measurements.append(measurement_info)
        
    return measurements
