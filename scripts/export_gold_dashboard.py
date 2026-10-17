"""Export the verified Gold Parquet tables to CSV for the static web dashboard.

Run from the repository root after the ETL pipeline completes:
    python scripts/export_gold_dashboard.py

CSV outputs are generated under web/data/ and are ignored by Git by default.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from pyspark.sql import SparkSession

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "gold"
OUTPUT = ROOT / "web" / "data"
TABLES = {
    "gold_daily_sales": "daily_sales.csv",
    "gold_product_performance": "product_performance.csv",
}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-in-git", action="store_true", help="Confirm intent to publish generated Gold CSVs.")
    args = parser.parse_args()
    missing = [str(GOLD / table) for table in TABLES if not (GOLD / table).exists()]
    if missing:
        raise FileNotFoundError("Gold Parquet table(s) not found. Run python src/run_pipeline.py first:\n" + "\n".join(missing))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    spark = SparkSession.builder.appName("ExportGoldForDashboard").master("local[*]").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    try:
        for table, filename in TABLES.items():
            frame = spark.read.parquet(str(GOLD / table))
            count = frame.count()
            frame.toPandas().to_csv(OUTPUT / filename, index=False)
            print(f"Exported {count:,} rows: {OUTPUT / filename}")
    finally:
        spark.stop()
    if args.include_in_git:
        print("Review generated CSVs and dataset terms before publishing.")
    else:
        print("CSV exports are ignored by Git by default. Publish them only after reviewing them and deliberately force-adding the files.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())