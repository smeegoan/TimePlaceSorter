
import re
from datetime import datetime
import exiftool

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

