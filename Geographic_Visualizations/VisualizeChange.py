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
# The two years to compare for visitor change analysis.
YEAR_A = "2019"  # The "before" year
YEAR_B = "2020"  # The "after" year

# 2. --- Input / Output Files ---
# Path to the GeoJSON file for the world map background.
INPUT_GEOJSON_PATH = Path("World_Continents.geojson")
# Path to the JSON file containing US National Park data.
INPUT_PARK_JSON_PATH = Path("USNP_data.json")
# Paths where the final map images will be saved.
OUTPUT_IMAGE_ABSOLUTE_PATH = Path(f"map_change_absolute_{YEAR_A}_vs_{YEAR_B}.png")
OUTPUT_IMAGE_PERCENT_PATH = Path(f"map_change_percent_{YEAR_A}_vs_{YEAR_B}.png")

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

def get_change_color(normalized_value: float) -> tuple:
    """
    Calculates a color from a diverging scale (-1 to +1 mapped to 0 to 1).
    0.0 -> Red (max decrease), 0.5 -> Neutral, 1.0 -> Purple (max increase).
    """
    t = normalized_value
    if t <= 0.5:
        # Negative side: Red (t=0) to Neutral (t=0.5)
        factor = t * 2.0  # Scale t from [0, 0.5] to [0, 1]
        r = int(204 + 28 * factor)
        g = int(0 + 232 * factor)
        b = int(0 + 232 * factor)
    else:
        # Positive side: Neutral (t=0.5) to Purple (t=1.0)
        factor = (t - 0.5) * 2.0  # Scale t from [0.5, 1] to [0, 1]
        r = int(232 - 125 * factor)
        g = int(232 - 188 * factor)
        b = int(232 - 87 * factor)
    return (r, g, b)

def generate_map(parks_with_colors: list, output_path: Path, base_map_image: Image.Image):
    """Draws parks on a base map and saves the result."""
    print(f"\n--- Generating Map: {output_path.name} ---")
    
    # Work on a copy to not modify the base image for the next run
    img = base_map_image.copy()
    draw = ImageDraw.Draw(img)
    
    SUPER_SAMPLED_SIZE = IMAGE_SIZE_PX * SUPER_SAMPLING_FACTOR
    view_scale = 1.0 / (1.0 - MARGIN_FRACTION)
    EARTH_RADIUS_KM = 6371.0
    globe_pixel_radius = (SUPER_SAMPLED_SIZE / 2.0) / view_scale
    park_pixel_radius = (PARK_CIRCLE_RADIUS_KM / EARTH_RADIUS_KM) * globe_pixel_radius

    # --- Set up 3D Rotation (re-calculated for clarity, could be passed in) ---
    target_vec = latlon_to_vec(PROJECTION_CENTER_LAT, PROJECTION_CENTER_LON)
    r_aim, _ = R.align_vectors([[0, 0, 1]], [target_vec])
    r_roll = R.from_euler('z', -CAMERA_ROLL_DEG, degrees=True)
    rotation = r_roll * r_aim

    visible_parks = 0
    for park in parks_with_colors:
        park_vec = latlon_to_vec(park['lat'], park['lon'])
        rotated_park_vec = rotation.apply(park_vec)

        if rotated_park_vec[2] > 0.0:
            visible_parks += 1
            x_proj, y_proj = rotated_park_vec[0], rotated_park_vec[1]
            px = (x_proj / view_scale + 1) * 0.5 * SUPER_SAMPLED_SIZE
            py = (-y_proj / view_scale + 1) * 0.5 * SUPER_SAMPLED_SIZE
            draw.ellipse([(px - park_pixel_radius, py - park_pixel_radius),
                          (px + park_pixel_radius, py + park_pixel_radius)],
                         fill=park['color'])
    print(f"▶ Drew {visible_parks} visible parks.")

    # --- Finalize and Save ---
    print("▶ Finalizing and saving image...")
    if SUPER_SAMPLING_FACTOR > 1:
        img = img.resize((IMAGE_SIZE_PX, IMAGE_SIZE_PX), Image.Resampling.LANCZOS)

    img.save(output_path)
    print(f"✅ Success! Map image saved to '{output_path}'")


def main():
    """Main function to generate and save the orthographic map image."""
    print(f"--- Program 2: Visitor Change Analysis ({YEAR_A} vs {YEAR_B}) ---")

    # --- 1. Validation and Setup ---
    if not INPUT_GEOJSON_PATH.exists():
        print(f"❌ ERROR: Input GeoJSON file not found at '{INPUT_GEOJSON_PATH}'")
        return
    OUTPUT_IMAGE_ABSOLUTE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUPER_SAMPLED_SIZE = IMAGE_SIZE_PX * SUPER_SAMPLING_FACTOR

    # --- 2. Load and Filter Park Data ---
    print("\nStep 1: Loading and filtering park data...")
    all_parks_data = load_park_data(INPUT_PARK_JSON_PATH)
    if not all_parks_data: return

    parks_for_analysis = []
    print(f"Filtering for parks with visitor data in BOTH '{YEAR_A}' and '{YEAR_B}'...")
    for park in all_parks_data:
        history = {e['year']: e['visitors'] for e in park.get('visitor_history', [])}
        if YEAR_A in history and YEAR_B in history:
            parks_for_analysis.append({
                "name": park.get('name', 'Unknown Park'),
                "lat": park['coordinates']['latitude'],
                "lon": park['coordinates']['longitude'],
                "visitors_a": history[YEAR_A],
                "visitors_b": history[YEAR_B]
            })
        else:
            print(f"  - Excluding '{park.get('name', 'Unknown Park')}': Missing required year data.")

    if not parks_for_analysis:
        print(f"\n❌ ERROR: No parks found with data for both {YEAR_A} and {YEAR_B}. Cannot generate maps.")
        return
    print(f"▶ Found {len(parks_for_analysis)} parks for analysis.")

    # --- 3. Generate Base Map (Done once to save time) ---
    print("\nStep 2: Generating base map image...")
    world_gdf = gpd.read_file(INPUT_GEOJSON_PATH)
    sindex = world_gdf.sindex
    
    target_vec = latlon_to_vec(PROJECTION_CENTER_LAT, PROJECTION_CENTER_LON)
    r_aim, _ = R.align_vectors([[0, 0, 1]], [target_vec])
    r_roll = R.from_euler('z', -CAMERA_ROLL_DEG, degrees=True)
    rotation = r_roll * r_aim
    
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
    base_map_image = Image.fromarray(output_image_array)
    print("▶ Base map generated.")

    # --- 4. Process and Generate ABSOLUTE Change Map ---
    print("\nStep 3: Processing data for ABSOLUTE change map...")
    for park in parks_for_analysis:
        park['delta'] = park['visitors_b'] - park['visitors_a']
    
    max_abs_delta = max(abs(p['delta']) for p in parks_for_analysis)
    if max_abs_delta == 0: max_abs_delta = 1.0

    parks_abs_colors = []
    for park in parks_for_analysis:
        # Normalize delta from [-max_abs_delta, +max_abs_delta] to [0, 1]
        normalized_delta = (park['delta'] / max_abs_delta) * 0.5 + 0.5
        parks_abs_colors.append({**park, 'color': get_change_color(normalized_delta)})
    
    generate_map(parks_abs_colors, OUTPUT_IMAGE_ABSOLUTE_PATH, base_map_image)

    # --- 5. Process and Generate PERCENT Change Map ---
    print("\nStep 4: Processing data for PERCENT change map...")
    parks_with_valid_percent = []
    for park in parks_for_analysis:
        if park['visitors_a'] > 0:
            percent_change = (park['visitors_b'] - park['visitors_a']) / park['visitors_a']
            parks_with_valid_percent.append({**park, 'percent_change': percent_change})
        else:
            print(f"  - Excluding '{park['name']}' from percent map: Cannot calculate % change from zero visitors in {YEAR_A}.")

    if parks_with_valid_percent:
        max_abs_percent = max(abs(p['percent_change']) for p in parks_with_valid_percent)
        if max_abs_percent == 0: max_abs_percent = 1.0

        parks_pct_colors = []
        for park in parks_with_valid_percent:
            # Normalize percent_change from [-max_abs_percent, +max_abs_percent] to [0, 1]
            normalized_percent = (park['percent_change'] / max_abs_percent) * 0.5 + 0.5
            parks_pct_colors.append({**park, 'color': get_change_color(normalized_percent)})
        
        generate_map(parks_pct_colors, OUTPUT_IMAGE_PERCENT_PATH, base_map_image)
    else:
        print("\n⚠️ WARNING: No parks had valid data for percent change calculation. Skipping percent map.")

    print("-" * 50)
    print("All tasks complete.")

if __name__ == "__main__":
    main()
