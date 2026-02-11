# GIS Geocoding Automation

This project demonstrates an automated GIS workflow for geocoding address data using Python and OpenStreetMap (Nominatim).

The script reads a CSV of addresses, geocodes them with built-in retry and timeout handling, keeps track of geocoding status, saves partial results to allow resuming interrupted runs, and exports both tabular and GIS-ready spatial outputs.

---

## Features

- Automated address geocoding using OpenStreetMap (Nominatim)
- Retry logic and timeout handling for unstable network responses
- Tracks geocoding status in a `STATUS` column (`Geocoded` / `Not Geocoded`)
- Resume-from-partial functionality to prevent data loss
- Incremental saving of partial results during processing
- Outputs both CSV and shapefile formats for GIS use
- Keeps non-geocoded addresses in the output for manual review
- Designed for real-world municipal and planning datasets

---

## Workflow Overview

1. Load raw address data from CSV
2. Automatically geocode addresses
3. Save progress incrementally to a partial CSV
4. Resume processing if interrupted
5. Export final results as:
   - Cleaned CSV with latitude/longitude and STATUS column
   - Shapefile for direct use in GIS software
   - All addresses are retained in outputs, even if geocoding fails

---

## Project Structure

```
Address_Geocoder/
├── data/
│ ├── input_addresses.csv # Raw input CSV (user-provided)
│ ├── geocoded_partial.csv # Auto-saved progress file
│ └── geocoded_final.csv # Final output CSV with LAT/LON + STATUS
│
├── shapefiles/
│ ├── geocoded_final.shp
│ ├── geocoded_final.shx
│ ├── geocoded_final.dbf
│ ├── geocoded_final.prj
│ └── geocoded_final.cpg
│
├── geocode_addresses.py # Main automation script
├── requirements.txt
└── README.md
```
## Requirements

- Python 3.9+
- pandas
- geopy
- geopandas
- shapely
- fiona
- pyproj

Install dependencies with:

```bash
pip install -r requirements.txt
```
## How to Run

1. Place your input CSV file in the `data/` folder.
2. Ensure the CSV contains an address column (e.g. `address`).
3. Run the script with optional arguments:

```bash
python geocode_addresses.py --input data/input_addresses.csv
```


### Optional Arguments

- `--partial` → Path for saving partial CSV (default: `geocoded_partial.csv`)
- `--output_csv` → Path for final CSV (default: `geocoded_final.csv`)
- `--output_shp` → Name of the shapefile (default: `geocoded_final.shp`)
- `--output_folder` → Folder to save shapefile output (default: `shapefiles`)

## Use Case

This workflow is designed for analysts working with large municipal,
planning, or operational datasets where manual geocoding is impractical.
It prioritizes reliability, reusability, and GIS ready outputs for use
in tools such as ArcGIS and QGIS.

## Notes

- This project respects OpenStreetMap Nominatim usage policies
- Requests are rate-limited to avoid service abuse
- For large production workloads, a hosted geocoding service is recommended

