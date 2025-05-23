import os
import argparse
from functools import partial
import shutil
from concurrent.futures import ThreadPoolExecutor
import google_location_history
import geonames
import metadata

def move_file(img_path, date, location, target_folder):
    filename = os.path.basename(img_path)
    target_img_path = os.path.join(target_folder, date, location)
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

def process_file(img_path, geonames_locations, geonames_tree, google_locations, google_history_start_tree, google_history_end_tree, target_folder):    
    (date_str, date) = metadata.get_photo_date(img_path)
    closest = google_location_history.find_closest_location(
        date, google_locations, google_history_start_tree, google_history_end_tree)
    google_history_coordinates = None if closest == None else google_location_history.extract_coordinates(
        closest, date)
    coordinates = metadata.get_gps_coordinates(img_path)
    if coordinates == None and google_history_coordinates != None:
        coordinates = google_history_coordinates
        metadata.set_gps_coordinates(img_path, coordinates)
    location = ""
    if coordinates and coordinates != None:
        lat, lon = coordinates
        closest = geonames.find_closest_location(
            lat, lon, geonames_locations, geonames_tree)
        if closest:
            location = closest['name']
        else:
            print("  Could not find a nearby location in the loaded data.")
    move_file(img_path, date_str, location, target_folder)

def parse_arguments():
    parser = argparse.ArgumentParser(description='Organize photos by date and location')
    parser.add_argument('--source-folder', '-s', 
                       default=r'D:\Pictures\Várias\tmp',
                       help='Source folder containing images (default: D:\\Pictures\\Várias\tmp)')
    parser.add_argument('--target-folder', '-t',
                       default=r'D:\Pictures\Várias', 
                       help='Target folder for organized images (default: D:\\Pictures\\Várias)')
    parser.add_argument('--google-location-history', '-g',
                       default='location-history.json',
                       help='Path to Google Location History JSON file (default: location-history.json)')
    return parser.parse_args()

# --- Main Script ---
if __name__ == "__main__":
    args = parse_arguments()
    
    # Configuration from command line arguments
    SOURCE_FOLDER = args.source_folder
    TARGET_FOLDER = args.target_folder
    GOOGLE_LOCATION_HISTORY_FILE = args.google_location_history
    GEONAMES_FOLDER = r'geonames'
    
    # Check if the image folders exist
    if not os.path.isdir(TARGET_FOLDER):
        print(f"Error: Target folder '{TARGET_FOLDER}' does not exist.")
        exit()
    if not os.path.isdir(SOURCE_FOLDER):
        print(f"Error: Source folder '{SOURCE_FOLDER}' does not exist.")
        exit()
    
    try:
        google_locations = google_location_history.load_records(
            GOOGLE_LOCATION_HISTORY_FILE)
        google_history_start_tree, google_history_end_tree = google_location_history.build_kdtree(
            google_locations)
    except FileNotFoundError:
        print(f"Google Location history not found at '{GOOGLE_LOCATION_HISTORY_FILE}'.")
        google_locations = None
        google_history_start_tree = None
        google_history_end_tree = None
    
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
    print(f"Source: {SOURCE_FOLDER}")
    print(f"Target: {TARGET_FOLDER}")
    print(f"Google Location History: {GOOGLE_LOCATION_HISTORY_FILE}")
    
    with ThreadPoolExecutor() as executor:
        executor.map(partial(
            process_file, 
            geonames_locations=geonames_locations, 
            geonames_tree=geonames_tree, 
            google_locations=google_locations, 
            google_history_start_tree=google_history_start_tree, 
            google_history_end_tree=google_history_end_tree,
            target_folder=TARGET_FOLDER), image_files)
    
    print("\nProcessing complete.")