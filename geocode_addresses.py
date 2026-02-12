import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from shapely.geometry import Point
import geopandas as gpd
import time
import os
import argparse
from datetime import datetime


def parse_arguments():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Geocode addresses CSV to CSV + GeoPackage/Shapefile"
    )
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument(
        "--output_name", default="geocoded_final",
        help="Base name for output files (no extension)"
    )
    parser.add_argument(
        "--output_folder", default="outputs",
        help="Folder to save all outputs (partial CSV, final CSV, spatial files)"
    )
    parser.add_argument(
        "--formats", default="GPKG",
        help="Comma-separated list of spatial formats to export (GPKG,SHP)"
    )
    return parser.parse_args()


def timestamp():
    """Return a timestamp string for filenames."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_data(input_path, partial_path):
    """
    Load CSV data. Resume from partial file if it exists.
    """
    if os.path.exists(partial_path):
        print("Loading partial CSV to resume...")
        df = pd.read_csv(partial_path)
    else:
        print(f"Loading raw CSV: {input_path}")
        df = pd.read_csv(input_path)
        df["LAT"] = None
        df["LON"] = None
        df["STATUS"] = "Not Geocoded"

    return df


def initialize_geocoder():
    """
    Initialize Nominatim geocoder with rate limiting.
    """
    geolocator = Nominatim(user_agent="geo_project", timeout=10)
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    return geocode


def geocode_address(geocode_func, address, max_attempts=3):
    """
    Attempt to geocode a single address with retry logic.
    """
    for attempt in range(max_attempts):
        try:
            location = geocode_func(address)
            return location
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for '{address}': {e}")
            time.sleep(2)

    print(f"Failed to geocode after {max_attempts} attempts: {address}")
    return None


def process_geocoding(df, geocode_func, partial_path):
    """
    Loop through DataFrame and geocode missing addresses.
    Saves partial progress every 10 records.
    """
    for idx, row in df.iterrows():

        if pd.notnull(row["LAT"]) and pd.notnull(row["LON"]):
            continue

        address = row["FULL_ADDRESS"]
        print(f"Geocoding {idx + 1}/{len(df)}: {address}")

        location = geocode_address(geocode_func, address)

        if location:
            df.at[idx, "LAT"] = location.latitude
            df.at[idx, "LON"] = location.longitude
            df.at[idx, "STATUS"] = "Geocoded"
        else:
            print(f"No match found for '{address}'")

        # Save partial progress
        if (idx + 1) % 10 == 0 or idx == len(df) - 1:
            df.to_csv(partial_path, index=False)
            print(f"Partial progress saved to {partial_path}")

    return df


def create_geodataframe(df):
    """
    Convert DataFrame to GeoDataFrame with geometry column.
    """
    if 'index' in df.columns:
        df = df.drop(columns=['index'])

    df["geometry"] = df.apply(
        lambda row: Point(row["LON"], row["LAT"])
        if pd.notnull(row["LAT"]) and pd.notnull(row["LON"])
        else None,
        axis=1
    )

    gdf = gpd.GeoDataFrame(
        df.reset_index(drop=True),
        geometry="geometry",
        crs="EPSG:4326"
    )

    return gdf


def save_outputs(df, gdf, output_folder, output_name, formats):
    """
    Save final CSV and spatial outputs (GeoPackage / Shapefile) with timestamp.
    """
    ts = timestamp()

    # Ensure output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Partial CSV path
    partial_path = os.path.join(output_folder, f"{output_name}_partial.csv")

    # Save final CSV
    final_csv_path = os.path.join(output_folder, f"{output_name}_{ts}.csv")
    df.to_csv(final_csv_path, index=False)
    print(f"Saved final CSV to {final_csv_path}")

    # Save spatial outputs
    for driver in formats:
        driver_upper = driver.strip().upper()
        if driver_upper not in ["GPKG", "SHP"]:
            print(f"Skipping unsupported format: {driver}")
            continue
        ext = "gpkg" if driver_upper == "GPKG" else "shp"
        spatial_path = os.path.join(output_folder, f"{output_name}_{ts}.{ext}")
        gdf.to_file(spatial_path, driver=driver_upper)
        print(f"Saved {driver_upper} file to {spatial_path}")

    return partial_path


def main():
    """
    Main workflow controller.
    """
    args = parse_arguments()

    # Parse formats argument
    formats = [fmt.strip() for fmt in args.formats.split(",")]

    # Ensure output folder exists
    if not os.path.exists(args.output_folder):
        os.makedirs(args.output_folder)

    # Path for partial CSV
    partial_csv_path = os.path.join(args.output_folder, f"{args.output_name}_partial.csv")

    # Load and geocode
    df = load_data(args.input, partial_csv_path)
    geocode_func = initialize_geocoder()
    df = process_geocoding(df, geocode_func, partial_csv_path)

    # Create GeoDataFrame
    gdf = create_geodataframe(df)

    # Save final outputs
    save_outputs(
        df,
        gdf,
        args.output_folder,
        args.output_name,
        formats
    )


if __name__ == "__main__":
    main()




