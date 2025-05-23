import json
from datetime import datetime
from pathlib import Path
from scipy.spatial import KDTree
from datetime import datetime, timedelta, timezone
import numpy as np
import json
from pathlib import Path


def load_records(filepath):
    """
    Load the JSON file and convert date strings to datetime and timestamp objects.
    Returns a list of dicts with extra fields:
    - start_dt, end_dt: datetime objects
    - start_ts, end_ts: timestamps (float)
    """
    print(f"Loading location data from {filepath}...")
    locations = json.loads(Path(filepath).read_text())
    for rec in locations:
        rec['start_dt'] = datetime.fromisoformat(
            rec['startTime'].replace('Z', '+00:00'))
        rec['end_dt'] = datetime.fromisoformat(
            rec['endTime'].replace('Z', '+00:00'))
        rec['start_ts'] = rec['start_dt'].timestamp()
        rec['end_ts'] = rec['end_dt'].timestamp()
    print(f"Loaded {len(locations)} locations.")
    return locations


def build_kdtree(records):
    """
    Build 1D KDTree for start_ts and end_ts.
    Returns two trees: one for starts and one for ends.
    """
    if KDTree is None:
        raise RuntimeError(
            "scikit-learn not installed: install with pip install scikit-learn")

    starts = np.array([[rec['start_ts']] for rec in records])
    ends = np.array([[rec['end_ts']] for rec in records])
    tree_start = KDTree(starts)
    tree_end = KDTree(ends)
    return tree_start, tree_end


def find_closest_location(target_dt, records, tree_start, tree_end):
    """
    Query the 1D KDTree for nearest neighbor on start_ts and end_ts.
    Returns the record with the minimal distance to target.
    """
    if target_dt == None or records == None:
        return None

    t = target_dt.timestamp()

    # If target is after all known end timestamps, return None
    max_end_ts = max(rec['end_ts'] for rec in records)
    min_end_ts = min(rec['start_ts'] for rec in records)
    if t > max_end_ts or t < min_end_ts:
        return None

    query = np.array([[t]])
    # Query nearest neighbor in both trees
    dist_s, ind_s = tree_start.query(query, k=1)
    dist_e, ind_e = tree_end.query(query, k=1)

    # Flatten and safely extract scalar distances and indices
    dist_s_val = float(dist_s.ravel()[0])
    dist_e_val = float(dist_e.ravel()[0])
    idx_s_val = int(ind_s.ravel()[0])
    idx_e_val = int(ind_e.ravel()[0])

    if dist_s_val <= dist_e_val:
        return records[idx_s_val]
    else:
        return records[idx_e_val]


def extract_coordinates(rec, target_datetime):
    """
    Extract coordinates from a record given a target datetime.
    - If it has 'visit.topCandidate.placeLocation', use it directly.
    - Else if it has 'timelinePath', return the point closest to the target datetime
      based on startTime + durationMinutesOffsetFromStartTime.
    Returns (latitude, longitude) tuple or None.
    """
    if target_datetime.tzinfo is None:
        target_datetime = target_datetime.replace(tzinfo=timezone.utc)
    point_str = None

    # Case 1: use visit.topCandidate.placeLocation directly
    if 'visit' in rec and 'topCandidate' in rec['visit']:
        point_str = rec['visit']['topCandidate'].get('placeLocation')

    # Case 2: calculate closest point in timelinePath
    elif 'timelinePath' in rec and rec['timelinePath']:
        try:
            start_time = datetime.fromisoformat(
                rec['startTime'].replace("Z", "+00:00"))
        except (KeyError, ValueError):
            return None

        closest_point = None
        min_diff = None

        for entry in rec['timelinePath']:
            try:
                offset = int(
                    entry.get('durationMinutesOffsetFromStartTime', 0))
                point_time = start_time + timedelta(minutes=offset)
                diff = abs((target_datetime - point_time).total_seconds())

                if min_diff is None or diff < min_diff:
                    min_diff = diff
                    closest_point = entry.get('point')
            except (ValueError, TypeError) as e:
                continue

        point_str = closest_point

    # Parse geo string
    if point_str and point_str.startswith('geo:'):
        try:
            lat_str, lon_str = point_str[4:].split(',')
            return float(lat_str), float(lon_str)
        except ValueError:
            return None

    return None
