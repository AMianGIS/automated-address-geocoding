import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from shapely.geometry import Point
import geopandas as gpd
import time
import os
import argparse

def main():
    # Set up command-line arguments
    parser = argparse.ArgumentParser(description="Geocode addresses CSV to CSV + Shapefile")
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--partial", default="geocoded_partial.csv", help="Path for partial CSV saves")
    parser.add_argument("--output_csv", default="geocoded_final.csv", help="Path for final CSV")
    parser.add_argument("--output_shp", default="geocoded_final.shp", help="Name of output Shapefile")
    parser.add_argument("--output_folder", default="shapefiles", help="Folder to save shapefile output")
    args = parser.parse_args()

    # Load CSV
    if os.path.exists(args.partial):
        print("Loading partial CSV to resume...")
        file = pd.read_csv(args.partial)
    else:
        print(f"Loading raw CSV: {args.input}")
        file = pd.read_csv(args.input)
        file["LAT"] = None
        file["LON"] = None
        file["STATUS"] = "Not Geocoded"  # Track status

    # Initialize geocoder
    geolocator = Nominatim(user_agent="geo_project", timeout=10)
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

    # Loop through addresses
    for x, row in file.iterrows():
        address = row["FULL_ADDRESS"]

        # Skip if already geocoded
        if pd.notnull(row["LAT"]) and pd.notnull(row["LON"]):
            continue

        print(f"Geocoding {x + 1}/{len(file)}: {address}")

        location = None
        for attempt in range(3):
            try:
                location = geocode(address)
                break
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for '{address}': {e}")
                time.sleep(2)
                if attempt == 2:
                    print(f"Failed to geocode after 3 attempts: {address}")

        # Record result
        if location:
            file.at[x, "LAT"] = location.latitude
            file.at[x, "LON"] = location.longitude
            file.at[x, "STATUS"] = "Geocoded"
        else:
            print(f"No match found for '{address}'")
            # STATUS remains "Not Geocoded"

        # Save partial CSV every 10 rows
        if (x + 1) % 10 == 0:
            file.to_csv(args.partial, index=False)

    # Save final CSV
    file.to_csv(args.output_csv, index=False)

    # Drop any old index column
    if 'index' in file.columns:
        file = file.drop(columns=['index'])

    # Create geometry column, keep None for missing coordinates
    file["geometry"] = file.apply(
        lambda row: Point(row["LON"], row["LAT"]) if pd.notnull(row["LAT"]) and pd.notnull(row["LON"]) else None,
        axis=1
    )

    # Create GeoDataFrame and reset index so FIDs start at 0
    gdf = gpd.GeoDataFrame(file.reset_index(drop=True), geometry="geometry", crs="EPSG:4326")

    # Ensure output folder exists
    if not os.path.exists(args.output_folder):
        os.makedirs(args.output_folder)

    # Full path for shapefile
    output_path = os.path.join(args.output_folder, args.output_shp)

    # Save GeoDataFrame
    gdf.to_file(output_path)
    print(f"Geocoding complete! Saved to {output_path}")

if __name__ == "__main__":
    main()





