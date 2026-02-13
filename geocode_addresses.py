import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from shapely.geometry import Point
import geopandas as gpd
import time
import os
import argparse
import logging
from datetime import datetime

def setup_logging(output_folder):
    """
    Configure logging to file and console.
    """
    log_path = os.path.join(output_folder, "geocode.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )

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

def validate_schema(df):
    """
    Ensure required columns exist and file is not empty.
    """
    required_columns = ["FULL_ADDRESS"]

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if df.empty:
        raise ValueError("Input CSV is empty.")

    return df

def load_data(input_path, partial_path):
    """
    Load CSV data. Resume from partial file if it exists.
    """
    if os.path.exists(partial_path):
        logging.info("Loading partial CSV to resume...")
        df = pd.read_csv(partial_path)
    else:
        logging.info(f"Loading raw CSV: {input_path}")
        df = pd.read_csv(input_path)
        df["LAT"] = None
        df["LON"] = None
        df["STATUS"] = "Not Geocoded"

    return df

def clean_addresses(df):
    """
    Normalize and clean FULL_ADDRESS column.
    """
    df["FULL_ADDRESS"] = (
        df["FULL_ADDRESS"]
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.replace(r",\s*,", ",", regex=True)
        .str.title()
    )

    # Remove empty strings after cleaning
    df = df[df["FULL_ADDRESS"].notna()]
    df = df[df["FULL_ADDRESS"].str.strip() != ""]
    return df

def remove_duplicates(df):
    """
    Remove duplicate FULL_ADDRESS entries.
    """
    before = len(df)
    df = df.drop_duplicates(subset="FULL_ADDRESS")
    after = len(df)
    logging.info(f"Removed {before - after} duplicate addresses.")
    return df

def generate_validation_report(original_count, df):
    """
    Log validation summary.
    """
    final_count = len(df)

    logging.info("Validation Summary")
    logging.info("------------------")
    logging.info(f"Original records: {original_count}")
    logging.info(f"Valid records: {final_count}")
    logging.info(f"Removed records: {original_count - final_count}")
    logging.info("------------------")


def run_validation_pipeline(df):
    """
    Run full validation and cleaning stage.
    """
    original_count = len(df)

    df = validate_schema(df)
    df = clean_addresses(df)
    df = remove_duplicates(df)

    generate_validation_report(original_count, df)

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
            logging.warning(f"Attempt {attempt + 1} failed for '{address}': {e}")
            time.sleep(2)

    logging.error(f"Failed to geocode after {max_attempts} attempts: {address}")
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
        logging.info(f"Geocoding {idx + 1}/{len(df)}: {address}")

        location = geocode_address(geocode_func, address)

        if location:
            df.at[idx, "LAT"] = location.latitude
            df.at[idx, "LON"] = location.longitude
            df.at[idx, "STATUS"] = "Geocoded"
        else:
            logging.warning(f"No match found for '{address}'")

        # Save partial progress
        if (idx + 1) % 10 == 0 or idx == len(df) - 1:
            df.to_csv(partial_path, index=False)
            logging.info(f"Partial progress saved to {partial_path}")

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
    logging.info(f"Saved final CSV to {final_csv_path}")

    # Save spatial outputs
    for driver in formats:
        driver_upper = driver.strip().upper()
        if driver_upper not in ["GPKG", "SHP"]:
            logging.info(f"Skipping unsupported format: {driver}")
            continue
        ext = "gpkg" if driver_upper == "GPKG" else "shp"
        spatial_path = os.path.join(output_folder, f"{output_name}_{ts}.{ext}")
        gdf.to_file(spatial_path, driver=driver_upper)
        logging.info(f"Saved {driver_upper} file to {spatial_path}")

    return partial_path


def main():
    args = parse_arguments()

    formats = [fmt.strip() for fmt in args.formats.split(",")]

    if not os.path.exists(args.output_folder):
        os.makedirs(args.output_folder)

    setup_logging(args.output_folder)

    partial_csv_path = os.path.join(
        args.output_folder,
        f"{args.output_name}_partial.csv"
    )

    # Load raw or partial data
    df = load_data(args.input, partial_csv_path)

    # 🔥 NEW: Validation Stage (only if starting fresh)
    if not os.path.exists(partial_csv_path):
        df = run_validation_pipeline(df)

    # Geocoding stage
    geocode_func = initialize_geocoder()
    df = process_geocoding(df, geocode_func, partial_csv_path)

    # Spatial stage
    gdf = create_geodataframe(df)

    # Export stage
    save_outputs(
        df,
        gdf,
        args.output_folder,
        args.output_name,
        formats
    )

if __name__ == "__main__":
    main()




