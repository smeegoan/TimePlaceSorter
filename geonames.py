import os
import glob  # To find files matching a pattern
import math  # For distance calculations (Haversine)
from scipy.spatial import KDTree

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

    a = math.sin(dLat / 2)**2 + math.cos(lat1) * \
        math.cos(lat2) * math.sin(dLon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance


def load_records(folder):
    """Loads relevant data from the GEONAMES_FOLDER"""
    locations = []
    geonames_files = glob.glob(os.path.join(folder, '*.txt'))
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
                                case "PPL" | "PPLA" | "PPLA2" | "PPLA3" | "PPLA5" | "PPLF" | "PPLG" | "PPLL" | "PPLQ" | "PPLS" | "PPLW" | "PPLX" | "ADM1" | "ADM1H" | "ADM2" | "ADM2H" | "ADM3" | "ADM3H" | "ADM4" | "ADM4H" | "ADM5" | "ADM5H" | "ADMD" | "ADMDH":
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
            print(
                f"Error: GeoNames file '{filepath}' not found. Please download suitable files from https://download.geonames.org/export/dump/")
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
    _, idx = tree.query((target_lat, target_lon))
    return locations[idx]

