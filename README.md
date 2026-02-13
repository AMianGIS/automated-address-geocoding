# GIS Geocoding Automation

This project demonstrates an automated GIS workflow for geocoding address data using Python and OpenStreetMap (Nominatim).

The script reads a CSV of addresses, geocodes them with built-in retry and timeout handling, tracks geocoding status, saves partial results to allow resuming interrupted runs, and exports both tabular and GIS-ready spatial outputs in modern formats (GeoPackage and Shapefile).

---

## Features

- Automated address geocoding using OpenStreetMap (Nominatim)
- Data validation stage: checks required columns and empty datasets
- Data cleaning stage: trims whitespace, collapses extra spaces, standardizes capitalization, and removes empty addresses
- Duplicate removal: prevents repeated geocoding of the same address
- Retry logic and timeout handling for unstable network responses
- Tracks geocoding status in a STATUS column (Geocoded / Not Geocoded)
- Resume-from-partial functionality to prevent data loss
- Incremental saving of partial results during processing
- Logging system for both console and file output (geocode.log)
- Outputs multiple spatial formats (GeoPackage .gpkg and Shapefile .shp)
- Timestamped filenames to avoid overwriting previous runs
- Designed for real-world municipal, planning, and operational datasets

---

## Workflow Overview

1. Load raw address data from CSV
2. Validate and clean addresses:
   - Check required column exists
   - Remove empty and invalid rows
   - Trim spaces and normalize capitalization
   - Remove duplicate addresses
3. Automatically geocode addresses with retry and timeout handling
4. Save progress incrementally to a partial CSV in the outputs/ folder
5. Resume processing if interrupted
6. Export final results as:
   - Timestamped CSV with latitude/longitude and STATUS column
   - GeoPackage (.gpkg) for modern GIS workflows
   - Shapefile (.shp) for legacy GIS compatibility
   
All outputs are saved in a central outputs/ folder.

---

## Project Structure

```
Address_Geocoder/
├── data/
│   └── sample_addresses.csv       # Raw input CSV (user-provided)
│
├── outputs/                      # Auto-generated output folder
│   ├── geocoded_final_partial.csv
│   ├── geocoded_final_20260212_142530.csv
│   ├── geocoded_final_20260212_142530.gpkg
│   ├── geocoded_final_20260212_142530.shp
│   └── geocode.log
│
├── geocode_addresses.py          # Main automation script
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

1. Place your input CSV file in the data/ folder.
   - Ensure it has a column for addresses (e.g., FULL_ADDRESS).
2. Run the script:
```bash
python geocode_addresses.py --input data/sample_addresses.csv
```


### Optional Arguments
| Argument          | Default          | Description                                                    |
| ----------------- | ---------------- | -------------------------------------------------------------- |
| `--output_name`   | `geocoded_final` | Base name for outputs                                          |
| `--output_folder` | `outputs`        | Folder to save outputs (partial CSV, final CSV, spatial files) |
| `--formats`       | `GPKG`           | Comma-separated list of spatial formats to export (`GPKG,SHP`) |

Example: Export both GeoPackage and Shapefile:
````bash
python geocode_addresses.py --input data/sample_addresses.csv --formats GPKG,SHP
````
## Use Case

This workflow is ideal for analysts working with municipal, planning, or operational datasets where manual geocoding is impractical. It prioritizes reliability, reproducibility, and GIS-ready outputs compatible with tools such as ArcGIS and QGIS.

## Notes

- Partial CSV progress is automatically saved in the outputs folder (*_partial.csv) to allow resuming interrupted runs.
- Final outputs are timestamped to avoid overwriting previous runs.
- Requests are rate-limited to respect OpenStreetMap Nominatim usage policies.
- For very large datasets, consider using a hosted geocoding service to handle volume efficiently.
- GeoPackage is the modern standard for GIS data; Shapefile support is included for legacy systems.