import os
import re
from datetime import datetime
from functools import partial
import exiftool
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
import google_location_history
import geonames

# --- Configuration ---
SOURCE_FOLDER = r'D:\Pictures\Várias'
TARGET_FOLDER = r'D:\Pictures\Várias'
GEONAMES_FOLDER = r'geonames'
GOOGLE_LOCATION_HISTORY_FILE = "location-history.json"
# --------------------


def set_gps_coordinates(filepath, coordinates):
    print(f"\nSetting photo coordinates to {coordinates}: {os.path.basename(filepath)}")
    latitude, longitude = coordinates
    lat_ref = 'N' if latitude >= 0 else 'S'
    lon_ref = 'E' if longitude >= 0 else 'W'
    lat = abs(latitude)
    lon = abs(longitude)

    tags = {
        'GPSLatitude': lat,
        'GPSLatitudeRef': lat_ref,
        'GPSLongitude': lon,
        'GPSLongitudeRef': lon_ref
    }

    with exiftool.ExifTool() as et:
        args = []
        for tag, value in tags.items():
            args.append(f"-{tag}={value}")
        args.append("-overwrite_original")
        args.append(filepath)
        et.execute(*args)


def get_gps_coordinates(filepath):
    with exiftool.ExifTool() as et:
        output = et.execute(b"-GPSLatitude", b"-GPSLongitude",
                            filepath.encode("utf-8"))
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
        return None


def set_photo_date(filepath, dt: datetime):
    print(f"\nSetting photo date to {dt}: {os.path.basename(filepath)}")
    exif_date = dt.strftime("%Y:%m:%d %H:%M:%S")

    with exiftool.ExifTool() as et:
        et.execute(
            b"-overwrite_original",
            f"-DateTimeOriginal={exif_date}".encode("utf-8"),
            filepath.encode("utf-8")
        )


def get_photo_date(filepath):
    with exiftool.ExifTool() as et:
        output = et.execute(b"-DateTimeOriginal", b"-CreateDate",
                            b"-XMP-microsoft:DateAcquired", filepath.encode("utf-8"))
        for line in output.splitlines():
            if any(key in line for key in ["Date/Time Original", "Create Date", "Date Acquired"]):
                date_str = line.split(": ", 1)[1].strip()
                # Convert the date string to datetime object
                try:
                    for fmt in ("%Y:%m:%d %H:%M:%S.%f", "%Y:%m:%d %H:%M:%S"):
                        try:
                            date_obj = datetime.strptime(date_str, fmt)
                            # Format as YYYY-MM-MMM
                            return (date_obj.strftime("%Y-%m-%b"), date_obj)
                        except ValueError:
                            continue
                except ValueError as v:
                    pass
 # ---- Fallback: file mod time ----
    try:
        date_obj = extract_datetime_from_filename(filepath)
        if date_obj == None:
            mod_time = os.path.getmtime(filepath)
            date_obj = datetime.fromtimestamp(mod_time)
        else:
            set_photo_date(filepath, date_obj)
        return (date_obj.strftime("%Y-%m-%b"), date_obj)
    except Exception as e:
        print(f"[Fallback] Failed to get file date for {filepath}: {e}")
        return (None, None)

def extract_datetime_from_filename(filename):
    # Try pattern with optional suffixes
    patterns = [
        # e.g. 2024-11-10_18-17-59-tlha2535
        r'(?P<date>\d{4}-\d{2}-\d{2})_(?P<time>\d{2}-\d{2}-\d{2})(?:-[\w\d]+)?',
        # e.g. 2014-10-06_05-09-48-9976
        r'(?P<date>\d{4}-\d{2}-\d{2})_(?P<time>\d{2}-\d{2}-\d{2})-\d+',
    ]

    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            date_part = match.group('date')
            time_part = match.group('time')
            dt = datetime.strptime(
                f"{date_part} {time_part}", "%Y-%m-%d %H-%M-%S")
            return dt

    raise None


def move_file(img_path, date, location):
    filename = os.path.basename(img_path)
    target_img_path = os.path.join(TARGET_FOLDER, date, location)
    os.makedirs(target_img_path, exist_ok=True)
    target_img_path = os.path.join(target_img_path, filename)
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


def process_file(img_path, geonames_locations, geonames_tree, google_locations, google_history_start_tree, google_history_end_tree):    
    (date_str, date) = get_photo_date(img_path)

    closest = google_location_history.find_closest_location(
        date, google_locations, google_history_start_tree, google_history_end_tree)

    google_history_coordinates = None if closest == None else google_location_history.extract_coordinates(
        closest, date)
    coordinates = get_gps_coordinates(img_path)
    if coordinates == None and google_history_coordinates != None:
        coordinates = google_history_coordinates
        set_gps_coordinates(img_path, coordinates)
    location = ""
    if coordinates and coordinates != None:
        lat, lon = coordinates
        closest = geonames.find_closest_location(
            lat, lon, geonames_locations, geonames_tree)

        if closest:
            # print(f"  Estimated location: {closest['name']}, {closest['country_code']} (distance: {haversine(lat, lon, closest['latitude'], closest['longitude']):.2f} km)")
            location = closest['name']
        else:
            print("  Could not find a nearby location in the loaded data.")
    move_file(img_path, date_str, location)

# --- Main Script ---


if __name__ == "__main__":
    # Check if the image folder exists
    if not os.path.isdir(TARGET_FOLDER):
        print(f"Error: Image folder '{TARGET_FOLDER}' does not exist.")
        exit()
    if not os.path.isdir(SOURCE_FOLDER):
        print(f"Error: Image folder '{SOURCE_FOLDER}' does not exist.")
        exit()

    try:
        google_locations = google_location_history.load_records(
            GOOGLE_LOCATION_HISTORY_FILE)
        google_history_start_tree, google_history_end_tree = google_location_history.build_kdtree(
            google_locations)
    except FileNotFoundError:
        print(f"Google Location history not found.")

    # Load GeoNames data (only once)
    geonames_locations = geonames.load_records(GEONAMES_FOLDER)
    geonames_tree, coords = geonames.build_kdtree(geonames_locations)

    if geonames_locations is None:
        print("Cannot continue without GeoNames data.")
        exit()

    image_files = [
        os.path.join(root, f)
        for root, _, files in os.walk(SOURCE_FOLDER)
        for f in files
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.heic', '.mp4', '.mov'))
    ]

    if not image_files:
        print(f"No image files found in {SOURCE_FOLDER}")
        exit()

    print(f"\nProcessing {len(image_files)} images...")

    with ThreadPoolExecutor() as executor:
        executor.map(partial(
            process_file, geonames_locations=geonames_locations, geonames_tree=geonames_tree, google_locations=google_locations, google_history_start_tree=google_history_start_tree, google_history_end_tree=google_history_end_tree), image_files)

    print("\nProcessing complete.")
