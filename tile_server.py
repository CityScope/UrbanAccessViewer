from fastapi import FastAPI
from starlette.responses import Response
from io import BytesIO
from PIL import Image
import numpy as np
from matplotlib import cm
import fiona
from shapely.geometry import shape, box
from shapely.strtree import STRtree
from shapely.ops import transform
from rasterio.features import rasterize
from pyproj import Transformer
import math

app = FastAPI()
vector_path = "States/illinois/level_of_service/population.gpkg"
layer_name = "population"
tilesize = 256  # Leaflet/Folium standard

with fiona.open(vector_path, layer=layer_name) as src:
    features = [feature for feature in src]
    geoms = [shape(f["geometry"]) for f in features]

transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
geoms_3857 = [transform(transformer.transform, g) for g in geoms]

tree = STRtree(geoms_3857)

def mercator_bounds(x, y, z):
    n = 2 ** z
    lon_left = x / n * 360.0 - 180.0
    lon_right = (x + 1) / n * 360.0 - 180.0
    lat_top = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    lat_bottom = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
    minx, miny = transformer.transform(lon_left, lat_bottom)
    maxx, maxy = transformer.transform(lon_right, lat_top)
    return (minx, miny, maxx, maxy)

@app.get("/tiles/{z}/{x}/{y}.png")
def get_tile(z: int, x: int, y: int):
    bounds = mercator_bounds(x, y, z)
    tile_box = box(*bounds)

    intersected = tree.query(tile_box)
    print(f"intersected")
    shapes_and_values = [(geom, 1) for geom in intersected if geom.intersects(tile_box)]

    if not shapes_and_values:
        tile_array = np.zeros((tilesize, tilesize), dtype=np.uint8)
    else:
        tile_array = rasterize(
            shapes_and_values,
            out_shape=(tilesize, tilesize),
            bounds=bounds,
            fill=0,
            dtype=np.uint8
        )

    # Alpha
    alpha = np.where(tile_array == 0, 0, 255).astype(np.uint8)

    # Colormap
    tile_norm = tile_array / (tile_array.max() + 1e-6)
    cmap = cm.get_cmap("coolwarm")
    tile_color = (cmap(tile_norm)[:, :, :3] * 255).astype(np.uint8)

    tile_rgba = np.dstack([tile_color, alpha])
    img = Image.fromarray(tile_rgba, mode="RGBA")

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png")
