import requests
import json
import time
import os

INPUT_FILE = "USNP_Park_URLs.json"
OUTPUT_FILE = "USNP_data.json"

REQUEST_DELAY_SECONDS = 10
MAX_RETRIES = 99
RETRY_DELAY_SECONDS = 10

# wikidata api endpoint and property IDs
API_ENDPOINT = "https://www.wikidata.org/w/api.php"
P_COORDINATES = "P625"
P_VISITORS_PER_YEAR = "P1174"
P_AREA = "P2046"
P_POINT_IN_TIME = "P585"

CONVERSION_TO_ACRES = {
    "acre": 1.0,
    "hectare": 2.47105,
    "square kilometre": 247.105,
    "square mile": 640.0
}

def get_wikidata_entity(entity_id: str) -> dict | None:
    """
    Fetches data for a Wikidata entity with retry logic.
    Returns the parsed JSON data or None if it fails after all retries.
    """
    params = {
        'action': 'wbgetentities',
        'ids': entity_id,
        'format': 'json',
        'props': 'claims|labels'
    }
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(API_ENDPOINT, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"  -> Network error for {entity_id}: {e}. Attempt {attempt + 1} of {MAX_RETRIES}.")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_SECONDS)
    
    print(f"  -> FAILED to fetch data for {entity_id} after {MAX_RETRIES} attempts.")
    return None

def get_unit_label(unit_url: str) -> str | None:
    """
    Given a unit URL, extracts the ID and fetches its English label.
    """
    if not unit_url or 'http' not in unit_url:
        return None
        
    unit_id = unit_url.split('/')[-1]
    unit_data = get_wikidata_entity(unit_id)
    if unit_data:
        try:
            return unit_data['entities'][unit_id]['labels']['en']['value']
        except KeyError:
            print(f"  -> Warning: Could not find English label for unit ID {unit_id}")
            return unit_id
    return None

def process_park(park_info: dict) -> dict | None:
    """
    Takes a park's basic info, fetches all extra data, converts area, and returns a complete dictionary.
    """
    park_id = park_info['id']
    data = get_wikidata_entity(park_id)

    if not data or 'entities' not in data or park_id not in data['entities']:
        return None

    try:
        claims = data['entities'][park_id]['claims']
    except KeyError:
        print(f"  -> No 'claims' data found for {park_info['name']} ({park_id}).")
        return None
    
    visitor_history = []
    for statement in claims.get(P_VISITORS_PER_YEAR, []):
        try:
            visitors = float(statement['mainsnak']['datavalue']['value']['amount'])
            year_str = statement['qualifiers'][P_POINT_IN_TIME][0]['datavalue']['value']['time']
            year = year_str[1:5]
            visitor_history.append({"year": year, "visitors": visitors})
        except (KeyError, IndexError):
            continue
    visitor_history.sort(key=lambda x: x['year'])
    
    coordinates = None
    if P_COORDINATES in claims:
        try:
            coord_data = claims[P_COORDINATES][0]['mainsnak']['datavalue']['value']
            coordinates = {"latitude": coord_data['latitude'], "longitude": coord_data['longitude']}
        except (KeyError, IndexError):
            print(f"  -> Warning: Could not parse coordinate data for {park_info['name']}.")
    
    area = None
    area_unit = None
    if P_AREA in claims:
        try:
            area_data = claims[P_AREA][0]['mainsnak']['datavalue']['value']
            area = float(area_data['amount'])
            unit_url = area_data.get('unit')
            
            if unit_url:
                area_unit = get_unit_label(unit_url)
            
            if area is not None and area_unit is not None:
                if area_unit in CONVERSION_TO_ACRES:
                    conversion_factor = CONVERSION_TO_ACRES[area_unit]
                    original_area = area
                    # convert and round to 2 decimal places
                    area = round(area * conversion_factor, 2)
                    print(f"  -> Converted {original_area} {area_unit} to {area} acres.")
                    area_unit = "acre" # The new unit is now 'acre'
                else:
                    # warning for an unrecognized unit
                    print(f"  -> WARNING: Unrecognized unit '{area_unit}' for {park_info['name']}. Cannot convert to acres. Storing original value.")
            
            elif area is not None and area_unit is None:
                print(f"  -> WARNING: Found area ({area}) for {park_info['name']} but could not determine its unit.")
                area_unit = "unknown"

        except (KeyError, IndexError):
            print(f"  -> Warning: Could not parse area data for {park_info['name']}.")
    
    new_park_data = {
        "name": park_info['name'],
        "id": park_id,
        "visitor_history": visitor_history,
        "coordinates": coordinates,
        "area": area,
        "area_unit": area_unit
    }
    return new_park_data

if __name__ == "__main__":
    if not os.path.exists(INPUT_FILE):
        print(f"FATAL: Input file not found at '{INPUT_FILE}'")
        exit()

    with open(INPUT_FILE, 'r') as f:
        input_data = json.load(f)
    
    parks_to_process = input_data.get('parks', [])
    total_parks = len(parks_to_process)
    
    print(f"Found {total_parks} parks to process from '{INPUT_FILE}'.\n")

    processed_parks = []
    success_count = 0
    failure_count = 0
    unconverted_units = set()

    for i, park in enumerate(parks_to_process):
        print(f"Processing park {i + 1}/{total_parks}: {park['name']} ({park['id']})")
        
        result = process_park(park)
        
        if result:
            processed_parks.append(result)
            success_count += 1
            if result.get('area_unit') and result['area_unit'] not in ["acre", "unknown", None]:
                unconverted_units.add(result['area_unit'])
        else:
            failure_count += 1
            print(f"  -> FAILED to process {park['name']}.")

        if i < total_parks - 1:
            print(f"--- Waiting for {REQUEST_DELAY_SECONDS} seconds... ---\n")
            time.sleep(REQUEST_DELAY_SECONDS)

    output_data = {"parks": processed_parks}

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print("\n" + "="*40)
    print("--- Processing Complete ---")
    print(f"Successfully wrote data to '{OUTPUT_FILE}'")
    print(f"Total parks in input: {total_parks}")
    print(f"Successfully processed: {success_count}")
    if failure_count > 0:
        print(f"Failed to process: {failure_count}")
    print("-" * 20)
    if unconverted_units:
        print("The following area units were found but NOT converted to acres:")
        for unit in sorted(list(unconverted_units)):
            print(f"  - {unit}")
    else:
        print("All area units were successfully converted to acres.")
    print("="*40)
