import os
import glob  # To find files matching a pattern
import math  # For distance calculations (Haversine)
import os
from datetime import datetime
from functools import partial
import exiftool
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from scipy.spatial import KDTree

# --- Configuration ---
SOURCE_FOLDER = r'D:\Pictures\Várias'
TARGET_FOLDER = r'D:\Pictures\Várias'
GEONAMES_FOLDER = r'geonames'

# --------------------

def get_gps_coordinates(filepath):
    with exiftool.ExifTool() as et:
        output = et.execute(b"-GPSLatitude", b"-GPSLongitude", filepath.encode("utf-8"))
        lat = lon = None
        for line in output.splitlines():
            if "GPS Latitude" in line:
                lat = line.split(": ", 1)[1].strip()
            elif "GPS Longitude" in line:
                lon = line.split(": ", 1)[1].strip()
        
        # Convert the string values to floats
        if lat and lon:
            lat = float(lat)
            lon = float(lon)
            return lat, lon
        return None, None

def get_photo_date(filepath):
    with exiftool.ExifTool() as et:
        output = et.execute(b"-DateTimeOriginal", b"-CreateDate", filepath.encode("utf-8"))
        for line in output.splitlines():
            if "Date/Time Original" in line:
                date_str = line.split(": ", 1)[1].strip()
                # Convert the date string to datetime object
                try:
                    date_obj = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                    # Format as YYYY-MM-MMM
                    return date_obj.strftime("%Y-%m-%b")  # Example: 2023-04-Apr
                except ValueError:
                    pass
            elif "Create Date" in line:
                date_str = line.split(": ", 1)[1].strip()
                # Convert the date string to datetime object
                try:
                    date_obj = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                    # Format as YYYY-MM-MMM
                    return date_obj.strftime("%Y-%m-%b")  # Example: 2023-04-Apr
                except ValueError:
                    pass
 # ---- Fallback: file mod time ----
    try:
        mod_time = os.path.getmtime(filepath)
        dt = datetime.fromtimestamp(mod_time)
        return dt.strftime("%Y-%m-%b")
    except Exception as e:
        print(f"[Fallback] Failed to get file date for {filepath}: {e}")
        return None


def build_kdtree(locations):
    """Builds a KDTree from the list of locations."""
    coords = [(loc['latitude'], loc['longitude']) for loc in locations]
    tree = KDTree(coords)
    return tree, coords  # coords needed to index back into locations


def haversine(lat1, lon1, lat2, lon2):
    """Calculates the 'as-the-crow-flies' distance between two points on Earth."""
    R = 6371  # Earth radius in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    a = math.sin(dLat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dLon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

def load_geonames_data():
    """Loads relevant data from the GeoNames allCountries.txt file."""
    locations = []
    geonames_files = glob.glob(os.path.join(GEONAMES_FOLDER, '*.txt'))
    for filepath in geonames_files:
        print(f"Loading location data from {filepath}...")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split('\t')
                    # Structure of allCountries.txt (may vary slightly):
                    # 0: geonameid, 1: name, 2: asciiname, 3: alternatenames,
                    # 4: latitude, 5: longitude, 6: feature class, 7: feature code,
                    # 8: country code, ... (other fields)
                    if len(parts) >= 9:
                        try:
                            lat = float(parts[4])
                            lon = float(parts[5])
                            name = parts[1]  # or parts[2] for ASCII name
                            country_code = parts[8]
                            # Could add feature_code (parts[7]) to filter by type (e.g., PPL=populated place)
                            match parts[7].removeprefix("'").removesuffix("'"):
                                case "PPL"| "PPLA"| "PPLA2"| "PPLA3"|"PPLA5"|"PPLF"| "PPLG"| "PPLL"|"PPLQ"| "PPLS"|"PPLW"|"PPLX"|"ADM1"| "ADM1H"| "ADM2"| "ADM2H"| "ADM3"| "ADM3H"| "ADM4"| "ADM4H"| "ADM5"| "ADM5H"| "ADMD"| "ADMDH":
                                    locations.append({
                                        'latitude': lat,
                                        'longitude': lon,
                                        'name': name,
                                        'country_code': country_code
                                    })
                        except ValueError:
                            # Ignore lines with invalid lat/lon format
                            continue
                        except IndexError:
                            # Ignore lines with insufficient columns
                            continue
            print(f"Loaded {len(locations)} locations.")
        except FileNotFoundError:
            print(f"Error: GeoNames file '{filepath}' not found.")
            return None
        except Exception as e:
            print(f"Error reading GeoNames file: {e}")
            return None
    return locations

def find_closest_location(target_lat, target_lon, locations, tree):
    """Finds the closest location using a KDTree."""
    if not locations or not tree:
        return None

    # KDTree expects (lat, lon)
    distance, idx = tree.query((target_lat, target_lon))
    return locations[idx]

def move_file(img_path, date, location):
    filename = os.path.basename(img_path)
    target_img_path = os.path.join(TARGET_FOLDER, date, location)
    os.makedirs(target_img_path, exist_ok=True)
    target_img_path = os.path.join(target_img_path,filename)
    if img_path.lower() == target_img_path.lower():
        return
    print(f" {img_path} → {target_img_path}")
    shutil.move(img_path, target_img_path)
    try:
        directory = os.path.dirname(img_path)
        os.rmdir(directory)
        print(f"Directory '{directory}' was removed successfully.")
    except OSError:            
        pass
    
def process_file(img_path, geonames_locations, tree):
    print(f"\nProcessing: {os.path.basename(img_path)}")

    date = get_photo_date(img_path)
    coordinates = get_gps_coordinates(img_path)
    location = ""
    if coordinates and coordinates != (None,None):
        lat, lon = coordinates        
        closest = find_closest_location(lat, lon, geonames_locations, tree)

        if closest:
                # print(f"  Estimated location: {closest['name']}, {closest['country_code']} (distance: {haversine(lat, lon, closest['latitude'], closest['longitude']):.2f} km)")
            location = closest['name']
        else:
            print("  Could not find a nearby location in the loaded data.")
    else:
        print(f"  No GPS coordinates found in the image.")
    move_file(img_path, date, location)
    
# --- Main Script ---

if __name__ == "__main__":
    # Check if the image folder exists
    if not os.path.isdir(TARGET_FOLDER):
        print(f"Error: Image folder '{TARGET_FOLDER}' does not exist.")
        exit()
    if not os.path.isdir(SOURCE_FOLDER):
        print(f"Error: Image folder '{SOURCE_FOLDER}' does not exist.")
        exit()        

    # Load GeoNames data (only once)
    geonames_locations = load_geonames_data()
    tree, coords = build_kdtree(geonames_locations)

    if geonames_locations is None:
        print("Cannot continue without GeoNames data.")
        exit()

    image_files = [
        os.path.join(root, f)
        for root, dirs, files in os.walk(SOURCE_FOLDER)
        for f in files
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.heic'))
    ]

    if not image_files:
        print(f"No image files found in {SOURCE_FOLDER}")
        exit()

    print(f"\nProcessing {len(image_files)} images...")

    with ThreadPoolExecutor() as executor:
        executor.map(partial(process_file, geonames_locations=geonames_locations, tree=tree), image_files)

    print("\nProcessing complete.")