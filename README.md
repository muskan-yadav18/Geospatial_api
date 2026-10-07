# Geospatial File Measurement API

A FastAPI backend service that accepts a geospatial file (Shapefile in `.zip` or `.kml`), processes the features within it, and returns measurement information.

## Setup

### Prerequisites
- Python 3.9+
- Recommended to use a virtual environment

### Installation

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone <repository_url>
   cd geospatial_api
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/MacOS:
   source venv/bin/activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

Run the development server using Uvicorn:
```bash
uvicorn app.main:app --reload
```

The API will be accessible at: `http://localhost:8000/`
Interactive API documentation (Swagger UI) will be at: `http://localhost:8000/docs`

## API Endpoints

### 1. Upload File
**POST** `/api/files/`

Uploads and processes a geospatial file.
- **Request Body**: `multipart/form-data` with a `file` field containing a `.zip` (Shapefile) or `.kml` file.
- **Example Response**:
```json
{
  "id": "abc12345-6789-def0-1234-56789abcdef0",
  "filename": "survey.kml",
  "feature_count": 120,
  "crs": "EPSG:4326",
  "status": "COMPLETED"
}
```

### 2. File Information
**GET** `/api/files/{id}/`

Returns information about the uploaded file.
- **Path Parameter**: `id` (string) - The UUID returned from the upload endpoint.
- **Example Response**: (Same as Upload File response)

### 3. Measurements
**GET** `/api/files/{id}/measurements/`

Returns measurements for the features in the file.
- **Path Parameter**: `id` (string) - The file UUID.
- **Example Response**:
```json
{
  "id": "abc12345-6789-def0-1234-56789abcdef0",
  "measurements": [
    {
      "feature_id": 0,
      "geometry_type": "Polygon",
      "properties": {
        "Name": "Parcel A",
        "Type": "Commercial"
      },
      "crs": "EPSG:4326",
      "measurement_type": "Area",
      "measurement_value": 4567.89,
      "unit": "Square Meters"
    },
    {
      "feature_id": 1,
      "geometry_type": "LineString",
      "properties": {
        "Name": "Road 1"
      },
      "crs": "EPSG:4326",
      "measurement_type": "Length",
      "measurement_value": 1234.56,
      "unit": "Meters"
    },
    {
      "feature_id": 2,
      "geometry_type": "Point",
      "properties": {
        "Name": "Well 1"
      },
      "crs": "EPSG:4326",
      "measurement_type": null,
      "measurement_value": null,
      "unit": null
    }
  ]
}
```

## Architecture

### Application Structure
The application follows a standard modular FastAPI structure:
- `app/main.py`: Application entry point.
- `app/api/endpoints.py`: Defines the HTTP routes and input/output schema handling.
- `app/services/geospatial.py`: Contains the core business logic for file parsing and metric calculation.
- `app/models/schemas.py`: Pydantic models for data validation and API documentation.

### File-Processing Flow
1. The user uploads a `.zip` or `.kml` file to the `/api/files/` endpoint.
2. The file is temporarily saved to disk.
3. `geopandas` (supported by `fiona`) reads the file into a `GeoDataFrame`.
4. Metadata (feature count, CRS) is extracted and stored in memory. The dataframe itself is also kept in memory (in a production system, this would be persisted to a database or blob storage).
5. The temporary file is cleaned up, and a unique `id` is returned.

### Measurement Calculation Flow
When the measurements API is hit:
1. The stored `GeoDataFrame` is retrieved.
2. If the Coordinate Reference System (CRS) is geographic (e.g., EPSG:4326), it is projected to an appropriate UTM projection to ensure measurements (area/length) are in meters and geometrically accurate.
3. The API iterates over the features. Polygons calculate `.area`, LineStrings calculate `.length`, and Points are ignored for measurements.
4. If an unsupported geometry type is found, it is gracefully bypassed without crashing.

### CRS Handling
Geographic CRSs (like WGS84 - EPSG:4326) measure in degrees, making raw Euclidean `.area` or `.length` operations highly inaccurate. The application solves this by dynamically reprojecting the data to a localized UTM (Universal Transverse Mercator) zone. This is achieved using `geopandas.GeoDataFrame.estimate_utm_crs()`, which selects the optimal EPSG code for the dataset's bounding box center, allowing for accurate Cartesian metric calculations.

## Design Decisions

- **FastAPI**: Selected for its speed, automatic interactive documentation (Swagger), and robust data validation via Pydantic.
- **Geopandas**: Chosen as the core geospatial engine because it efficiently wraps `shapely` and `fiona` and provides high-level DataFrame abstractions that make projection and measurement operations concise.
- **In-Memory Storage**: Implemented for simplicity and speed in this assignment context. A production implementation would use a relational spatial database like PostGIS.
- **Dynamic UTM Estimation**: Hardcoding a metric projection (like Web Mercator EPSG:3857) introduces large distortions away from the equator. Using `estimate_utm_crs()` provides a much more accurate localized metric measurement for area and length without requiring user input.

## Learning and Future Scope

- **Learning**: Implementing this reinforced best practices for building decoupled FastAPI services and handling spatial abstractions efficiently using `geopandas`.
- **Future Scope**: 
  - Integrating PostgreSQL + PostGIS to persist spatial data instead of holding DataFrames in memory.
  - Adding asynchronous background tasks (e.g. using Celery) for processing extremely large shapefiles to prevent HTTP timeout.
  - Supporting more file types like GeoJSON or GeoTIFF (for raster processing).
  - Enabling Dockerization via a `Dockerfile` to simplify the installation of system-level spatial dependencies like GDAL/GEOS.
