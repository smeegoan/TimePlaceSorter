# Media Renamer

**Media Renamer** is a Python tool designed to rename media files based on their metadata, specifically the date and GPS information embedded within them. This is particularly useful for organizing photos and videos by the time and location they were taken.

## Features

- **Date-Based Renaming**: Extracts the creation date from media metadata to rename files accordingly.
- **GPS-Based Renaming**: Utilizes GPS coordinates from media metadata to include location information in filenames.
- **Reverse Geocoding**: Translates GPS coordinates into human-readable locations using reverse geocoding techniques.
- **Batch Processing**: Processes multiple files in a specified directory, streamlining the renaming process.
- **Google Location History GeoCoding**: Utilizes GPS coordinates from Google Location Hisotry to include location information in media metadata and file names.

## Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/smeegoan/media-renamer.git
   cd media-renamer
   ```

2. **Install Dependencies**:

   Ensure you have Python 3 installed. Then, install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Prepare Your Media Files**:

   Place the media files you wish to rename into a directory.

2. **Run the Script**:

   Execute the `reverse_geocoding.py` script, specifying the path to your media directory:

   ```bash
   python reverse_geocoding.py /path/to/media/files
   ```

   The script will process each file, extract the relevant metadata, perform reverse geocoding for GPS data, and rename the files accordingly.

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/smeegoan/media-renamer/blob/main/LICENSE) file for details.

