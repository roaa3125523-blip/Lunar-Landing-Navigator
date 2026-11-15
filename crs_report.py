from pathlib import Path
import rasterio

project = Path(__file__).parent

files = (
    list(project.glob("*.tif"))
    + list(project.glob("*.tiff"))
    + list((project / "data").glob("*.tif"))
    + list((project / "data").glob("*.tiff"))
)

if not files:
    raise FileNotFoundError("No TIFF file found.")

dem_file = files[0]

with rasterio.open(dem_file) as dem:
    print("FILE:", dem_file.name)
    print("CRS:")
    print(dem.crs)
    print("\nFULL CRS DEFINITION:")
    print(dem.crs.to_wkt() if dem.crs else "Missing CRS")

    print("\nWIDTH:", dem.width)
    print("HEIGHT:", dem.height)
    print("BOUNDS:", dem.bounds)
    print("TRANSFORM:", dem.transform)
    print("PIXEL SIZE:", dem.res)

    values = dem.read(1, masked=True)
    print("VALID PIXELS:", values.count())
    print("MIN ELEVATION:", values.min())
    print("MAX ELEVATION:", values.max())