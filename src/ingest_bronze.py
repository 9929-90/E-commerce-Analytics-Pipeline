
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"

FILES = [
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_customers_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_products_dataset.csv",
]


def ingest_file(filename: str) -> None:
    source_path = RAW_DIR / filename

    if not source_path.exists():
        raise FileNotFoundError(f"Missing source file: {source_path}")

    # Read the source without changing its column types deliberately.
    df = pd.read_csv(source_path)

    # Add metadata for traceability.
    df["_source_file"] = filename
    df["_ingested_at_utc"] = datetime.now(timezone.utc).isoformat()

    # Keep each source dataset in its own Bronze directory.
    table_name = filename.removesuffix(".csv").replace(
        "olist_", ""
    ).replace("_dataset", "")

    output_dir = BRONZE_DIR / table_name
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "data.parquet"
    df.to_parquet(output_path, index=False)

    # Read the output back to verify the write.
    saved_df = pd.read_parquet(output_path)

    if len(saved_df) != len(df):
        raise ValueError(f"Row count mismatch for {filename}")

    print(
        f"SUCCESS | {filename} | "
        f"Rows: {len(saved_df):,} | "
        f"Output: {output_path}"
    )


def main() -> None:
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)

    for filename in FILES:
        ingest_file(filename)

    print("\nBronze ingestion completed.")


if __name__ == "__main__":
    main()
