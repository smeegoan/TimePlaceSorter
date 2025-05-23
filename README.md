# TimePlaceSorter

**TimePlaceSorter** is a Python tool that organizes and renames media files based on their metadata—specifically creation date and GPS location. It’s designed to help you sort and name photos and videos by the time and place they were taken, even supplementing missing GPS data using Google Location History.

## Features

- **Date-Based Renaming**: Extracts the creation date from media metadata to organize files chronologically.
- **Location-Based Renaming**: Uses embedded GPS data to include location names in filenames.
- **Reverse Geocoding via GeoNames**: Converts GPS coordinates into readable location names (e.g., city or locality).
- **Google Location History Integration**: Supplements missing GPS metadata using your Google Location History export, and optionally updates media metadata with this info.
- **Batch Processing**: Recursively scans a source folder and processes all supported media files.
- **Threaded Execution**: Utilizes multithreading for efficient processing of large batches.

## Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/smeegoan/media-renamer.git
   cd media-renamer
   ```

2. **Install Dependencies**:

   Ensure Python 3 is installed, then run:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

```bash
python reverse_geocoding.py [OPTIONS]
```

### Command-Line Options

| Argument | Description | Default |
|----------|-------------|---------|
| `--source-folder`, `-s` | Path to folder with source media files | `D:\Pictures\Várias	mp` |
| `--target-folder`, `-t` | Path to destination folder where files will be organized | `D:\Pictures\Várias` |
| `--google-location-history`, `-g` | Path to your Google Location History JSON file | `location-history.json` |

### Example

```bash
python reverse_geocoding.py -s ./input_media -t ./organized_media -g ~/Downloads/LocationHistory.json
```

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/smeegoan/media-renamer/blob/main/LICENSE) file for details.
