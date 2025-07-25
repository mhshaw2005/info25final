import geopandas as gpd
import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path
import time
import json
from shapely.geometry import Point
from scipy.spatial.transform import Rotation as R
from tqdm import tqdm

# ==============================================================================
# --- CONFIGURATION ---
# ==============================================================================

# 1. --- Analysis Settings ---
# The year to analyze from the park data JSON file.
TARGET_YEAR = "2010"

# 2. --- Input / Output Files ---
# Path to the GeoJSON file for the world map background.
INPUT_GEOJSON_PATH = Path("World_Continents.geojson")
# Path to the JSON file containing US National Park data.
INPUT_PARK_JSON_PATH = Path("USNP_data.json")
# Path where the final map image will be saved.
OUTPUT_IMAGE_PATH = Path(f"map_visitors_{TARGET_YEAR}.png")

# 3. --- Image and Quality Settings ---
IMAGE_SIZE_PX = 2048
SUPER_SAMPLING_FACTOR = 2

# 4. --- Projection and View Settings ---
# Centered on the United States for better visibility of the data.
PROJECTION_CENTER_LAT = 45
PROJECTION_CENTER_LON = -105
CAMERA_ROLL_DEG = -13
MARGIN_FRACTION = 0.05

# 5. --- Visual Style ---
LAND_COLOR = (78, 97, 65)
OCEAN_COLOR = (130, 160, 194)
SPACE_COLOR = (10, 15, 20)
# The radius of the circles used to represent parks, in kilometers.
PARK_CIRCLE_RADIUS_KM = 50

# ==============================================================================
# --- SCRIPT LOGIC ---
# You should not need to edit anything below this line.
# ==============================================================================

def latlon_to_vec(lat, lon):
    """Converts latitude and longitude to a 3D unit vector."""
    lat_rad = np.deg2rad(lat)
    lon_rad = np.deg2rad(lon)
    x = np.cos(lat_rad) * np.cos(lon_rad)
    y = np.cos(lat_rad) * np.sin(lon_rad)
    z = np.sin(lat_rad)
    return np.array([x, y, z])

def load_park_data(filepath: Path) -> list | None:
    """Loads and validates park data from the specified JSON file."""
    if not filepath.exists():
        print(f"❌ ERROR: Park data file not found at '{filepath}'")
        return None
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        if 'parks' not in data or not isinstance(data['parks'], list):
            raise KeyError
        return data['parks']
    except (json.JSONDecodeError, KeyError):
        print(f"❌ ERROR: File '{filepath}' is not a valid JSON or is missing the 'parks' key.")
        return None

def get_visitor_color(normalized_value: float) -> tuple:
    """Calculates a color based on a normalized value (0.0 to 1.0)."""
    t = normalized_value
    if t <= 0.7:
        # Gradient from Yellow (t=0) to Orange (t=0.7)
        r = 255
        g = int(255 * (0.7 - t) / 0.7)
        b = 0
    else:
        # Gradient from Orange (t=0.7) to a darker Red (t=1.0)
        r = int(255 - 116 * (t - 0.7) / 0.3)
        g = 0
        b = 0
    return (r, g, b)

def main():
    """Main function to generate and save the orthographic map image."""
    print(f"--- Program 1: Generating Map for {TARGET_YEAR} Park Visitors ---")

    # --- 1. Validation and Setup ---
    if not INPUT_GEOJSON_PATH.exists():
        print(f"❌ ERROR: Input GeoJSON file not found at '{INPUT_GEOJSON_PATH}'")
        return
    OUTPUT_IMAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUPER_SAMPLED_SIZE = IMAGE_SIZE_PX * SUPER_SAMPLING_FACTOR

    # --- 2. Load and Filter Park Data ---
    print("\nStep 1: Loading and filtering park data...")
    all_parks_data = load_park_data(INPUT_PARK_JSON_PATH)
    if not all_parks_data:
        return

    parks_for_analysis = []
    print(f"Filtering for parks with visitor data in '{TARGET_YEAR}'...")
    for park in all_parks_data:
        visitor_history = {entry['year']: entry['visitors'] for entry in park.get('visitor_history', [])}
        if TARGET_YEAR in visitor_history:
            parks_for_analysis.append({
                "name": park.get('name', 'Unknown Park'),
                "lat": park['coordinates']['latitude'],
                "lon": park['coordinates']['longitude'],
                "visitors": visitor_history[TARGET_YEAR]
            })
        else:
            print(f"  - Excluding '{park.get('name', 'Unknown Park')}': Missing {TARGET_YEAR} data.")

    if not parks_for_analysis:
        print(f"\n❌ ERROR: No parks found with data for the year {TARGET_YEAR}. Cannot generate map.")
        return

    print(f"▶ Found {len(parks_for_analysis)} parks for analysis.")

    # --- 3. Normalize Data and Assign Colors ---
    print("\nStep 2: Normalizing visitor data and assigning colors...")
    visitor_counts = [p['visitors'] for p in parks_for_analysis]
    min_visitors, max_visitors = min(visitor_counts), max(visitor_counts)
    visitor_range = float(max_visitors - min_visitors)
    if visitor_range == 0: visitor_range = 1.0 # Avoid division by zero

    for park in parks_for_analysis:
        normalized_visitors = (park['visitors'] - min_visitors) / visitor_range
        park['color'] = get_visitor_color(normalized_visitors)
    print("▶ Park colors calculated based on visitor counts.")

    # --- 4. Load Geospatial Data for Base Map ---
    print("\nStep 3: Loading geospatial data for base map...")
    world_gdf = gpd.read_file(INPUT_GEOJSON_PATH)
    sindex = world_gdf.sindex
    print(f"▶ Loaded {len(world_gdf)} features.")

    # --- 5. Set up 3D Rotation ---
    print("\nStep 4: Calculating camera rotation...")
    target_vec = latlon_to_vec(PROJECTION_CENTER_LAT, PROJECTION_CENTER_LON)
    r_aim, _ = R.align_vectors([[0, 0, 1]], [target_vec])
    r_roll = R.from_euler('z', -CAMERA_ROLL_DEG, degrees=True)
    rotation = r_roll * r_aim
    print("▶ 'Look-at' rotation calculated.")

    # --- 6. Generate Base Map (Ray-Casting) ---
    print("\nStep 5: Generating base map image via ray-casting...")
    view_scale = 1.0 / (1.0 - MARGIN_FRACTION)
    x = np.linspace(-view_scale, view_scale, SUPER_SAMPLED_SIZE)
    y = np.linspace(view_scale, -view_scale, SUPER_SAMPLED_SIZE)
    xx, yy = np.meshgrid(x, y)

    radius_sq = xx**2 + yy**2
    on_globe_mask = radius_sq <= 1.0
    zz = np.sqrt(1 - radius_sq[on_globe_mask])
    visible_points_3d = np.vstack((xx[on_globe_mask], yy[on_globe_mask], zz)).T

    rotated_points_3d = rotation.inv().apply(visible_points_3d)
    lon_rad = np.arctan2(rotated_points_3d[:, 1], rotated_points_3d[:, 0])
    lat_rad = np.arcsin(rotated_points_3d[:, 2])
    lon_deg = np.rad2deg(lon_rad)
    lat_deg = np.rad2deg(lat_rad)

    point_colors = np.zeros((len(lon_deg), 3), dtype=np.uint8)
    for i in tqdm(range(len(lon_deg)), desc="  - Coloring pixels"):
        point = Point(lon_deg[i], lat_deg[i])
        possible_matches_index = list(sindex.intersection(point.bounds))
        if possible_matches_index and world_gdf.iloc[possible_matches_index].contains(point).any():
            point_colors[i] = LAND_COLOR
        else:
            point_colors[i] = OCEAN_COLOR

    output_image_array = np.full((SUPER_SAMPLED_SIZE, SUPER_SAMPLED_SIZE, 3), SPACE_COLOR, dtype=np.uint8)
    output_image_array[on_globe_mask] = point_colors
    img = Image.fromarray(output_image_array)
    print("▶ Base map generated.")

    # --- 7. Draw Park Data on Top ---
    print("\nStep 6: Drawing park locations on map...")
    draw = ImageDraw.Draw(img)
    EARTH_RADIUS_KM = 6371.0
    globe_pixel_radius = (SUPER_SAMPLED_SIZE / 2.0) / view_scale
    park_pixel_radius = (PARK_CIRCLE_RADIUS_KM / EARTH_RADIUS_KM) * globe_pixel_radius

    visible_parks = 0
    for park in parks_for_analysis:
        park_vec = latlon_to_vec(park['lat'], park['lon'])
        rotated_park_vec = rotation.apply(park_vec)

        # Check if on visible hemisphere (z > 0)
        if rotated_park_vec[2] > 0.0:
            visible_parks += 1
            x_proj, y_proj = rotated_park_vec[0], rotated_park_vec[1]

            # Convert projected 3D coordinates to 2D pixel coordinates
            px = (x_proj / view_scale + 1) * 0.5 * SUPER_SAMPLED_SIZE
            py = (-y_proj / view_scale + 1) * 0.5 * SUPER_SAMPLED_SIZE

            draw.ellipse([(px - park_pixel_radius, py - park_pixel_radius),
                          (px + park_pixel_radius, py + park_pixel_radius)],
                         fill=park['color'])
    print(f"▶ Drew {visible_parks} visible parks.")

    # --- 8. Finalize and Save ---
    print("\nStep 7: Finalizing and saving image...")
    if SUPER_SAMPLING_FACTOR > 1:
        print(f"  - Downscaling image from {SUPER_SAMPLED_SIZE}px to {IMAGE_SIZE_PX}px...")
        img = img.resize((IMAGE_SIZE_PX, IMAGE_SIZE_PX), Image.Resampling.LANCZOS)

    img.save(OUTPUT_IMAGE_PATH)
    print("-" * 50)
    print(f"✅ Success! Map image saved to '{OUTPUT_IMAGE_PATH}'")
    print("-" * 50)

if __name__ == "__main__":
    main()
