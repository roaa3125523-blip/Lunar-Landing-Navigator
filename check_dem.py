from pathlib import Path
import rasterio
from pyproj import Transformer

project_folder = Path(__file__).parent
files = (
    list(project_folder.glob("*.tif"))
    + list(project_folder.glob("*.tiff"))
)

if not files:
    print("TIFF file not found")
    raise SystemExit

with rasterio.open(files[0]) as dem:
    print("CRS:", dem.crs)
    print("Bounds:", dem.bounds)

    # Site04 - Shackleton Rim
    latitude = -89.7668
    longitude = 188.13

    transformer = Transformer.from_crs(
        "EPSG:4326",
        dem.crs,
        always_xy=True
    )

    x, y = transformer.transform(longitude, latitude)

    print("Site04 projected X:", x)
    print("Site04 projected Y:", y)

    inside = (
        dem.bounds.left <= x <= dem.bounds.right
        and dem.bounds.bottom <= y <= dem.bounds.top
    )

    print("Is Site04 inside this DEM?", inside)