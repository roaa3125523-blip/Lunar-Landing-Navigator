from pathlib import Path
import rasterio
import pandas as pd

PROJECT = Path(__file__).resolve().parent
DEM_FOLDER = PROJECT / "data" / "DEM"

results = []

for file in sorted(DEM_FOLDER.glob("*_surf.tif")):
    with rasterio.open(file) as src:
        results.append({
            "site": file.stem.replace("_surf", ""),
            "crs": str(src.crs),
            "width": src.width,
            "height": src.height,
            "pixel_size_x": src.transform.a,
            "pixel_size_y": src.transform.e,
            "origin_x": src.transform.c,
            "origin_y": src.transform.f,
            "nodata": src.nodata,
            "bounds": str(src.bounds),
            "min_elevation": float(src.read(1).min()),
            "max_elevation": float(src.read(1).max())
        })

df = pd.DataFrame(results)

output = PROJECT / "results" / "dem_metadata.csv"
output.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(output, index=False)

print("\nDEM METADATA CHECK")
print(df.to_string(index=False))
print(f"\nSaved to: {output}")