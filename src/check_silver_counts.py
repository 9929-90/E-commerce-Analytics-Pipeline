
from pathlib import Path
from pyspark.sql import SparkSession

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SILVER_DIR = PROJECT_ROOT / "data" / "silver"

spark = (
    SparkSession.builder
    .appName("CheckSilverCounts")
    .master("local[*]")
    .getOrCreate()
)

tables = [
    "orders",
    "customers",
    "order_items",
    "order_payments",
]

try:
    for table in tables:
        print(f"\n{'=' * 50}")
        print(f"TABLE: {table}")
        print("=" * 50)

        for layer in [
            table,
            f"quarantine/{table}",
        ]:
            path = SILVER_DIR / layer

            if path.exists() and any(path.glob("*.parquet")):
                count = spark.read.parquet(str(path)).count()
                print(f"{layer}: {count} rows")
            else:
                print(f"{layer}: No Parquet files found")
finally:
    spark.stop()
