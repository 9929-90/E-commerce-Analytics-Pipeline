from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

ROOT = Path(__file__).resolve().parent.parent
GOLD = ROOT / "data" / "gold" / "gold_product_performance"

spark = (
    SparkSession.builder
    .appName("ValidateGoldProductPerformance")
    .master("local[*]")
    .config("spark.sql.session.timeZone", "UTC")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")

failures = []

def check(condition, passed_message, failed_message):
    if condition:
        print(f"PASS: {passed_message}")
    else:
        print(f"FAIL: {failed_message}")
        failures.append(failed_message)

try:
    if not GOLD.exists():
        raise FileNotFoundError(f"Gold table not found: {GOLD}")

    gold = spark.read.parquet(str(GOLD))
    gold_count = gold.count()

    check(gold_count > 0, f"Gold table has {gold_count} rows",
          "Gold table is empty")

    required = {
        "product_id", "product_category_name", "units_sold",
        "total_orders", "product_revenue", "freight_revenue",
        "total_revenue"
    }
    check(required.issubset(set(gold.columns)),
          "All required Gold columns exist",
          f"Missing columns: {required - set(gold.columns)}")

    if required.issubset(set(gold.columns)):
        check(
            gold.filter(F.col("product_id").isNull()).count() == 0,
            "No null product IDs",
            "Null product IDs found",
        )

        check(
            gold.groupBy("product_id").count()
                .filter(F.col("count") > 1).count() == 0,
            "One row per product ID",
            "Duplicate product IDs found",
        )

        check(
            gold.filter(
                (F.col("units_sold") < 0) |
                (F.col("total_orders") < 0)
            ).count() == 0,
            "No negative unit or order counts",
            "Negative unit or order counts found",
        )

        check(
            gold.filter(
                (F.col("product_revenue") < -0.000001) |
                (F.col("freight_revenue") < -0.000001) |
                (F.col("total_revenue") < -0.000001)
            ).count() == 0,
            "No negative revenue values",
            "Negative revenue values found",
        )

        mismatch = gold.filter(
            F.abs(
                F.col("total_revenue") -
                F.col("product_revenue") -
                F.col("freight_revenue")
            ) > 0.01
        ).count()

        check(
            mismatch == 0,
            "Total revenue equals product revenue plus freight",
            f"{mismatch} rows have inconsistent revenue totals",
        )

        count_mismatch = gold.filter(
            (F.col("units_sold") == 0) &
            (F.col("total_orders") != 0)
        ).count()

        check(
            count_mismatch == 0,
            "Products with zero units have zero orders",
            f"{count_mismatch} rows have inconsistent zero-unit counts",
        )

    if failures:
        print(f"\nVALIDATION FAILED: {len(failures)} check(s)")
        raise SystemExit(1)

    print("\nALL GOLD PRODUCT-PERFORMANCE CHECKS PASSED")

finally:
    spark.stop()
