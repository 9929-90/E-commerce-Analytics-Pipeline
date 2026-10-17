
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    count,
    countDistinct,
    sum as spark_sum,
    abs as spark_abs,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SILVER_DIR = PROJECT_ROOT / "data" / "silver"
GOLD_PATH = PROJECT_ROOT / "data" / "gold" / "gold_daily_sales"

spark = (
    SparkSession.builder
    .appName("ValidateGoldDailySales")
    .master("local[*]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

try:
    gold = spark.read.parquet(str(GOLD_PATH))
    orders = spark.read.parquet(str(SILVER_DIR / "orders"))
    items = spark.read.parquet(str(SILVER_DIR / "order_items"))

    # 1. Gold table must contain records
    gold_count = gold.count()
    assert gold_count > 0, "FAIL: Gold table is empty"
    print(f"PASS: Gold table contains {gold_count} daily records")

    # 2. Each date must appear only once
    duplicate_dates = (
        gold.groupBy("order_date")
        .count()
        .filter(col("count") > 1)
        .count()
    )
    assert duplicate_dates == 0, "FAIL: Duplicate order dates found"
    print("PASS: No duplicate order dates")

    # 3. Important fields must not be null
    null_rows = gold.filter(
        col("order_date").isNull()
        | col("total_orders").isNull()
        | col("total_product_sales").isNull()
        | col("total_freight").isNull()
        | col("total_sales").isNull()
    ).count()

    assert null_rows == 0, f"FAIL: {null_rows} rows contain nulls"
    print("PASS: No null values in required Gold columns")

    # 4. Order counts must be positive
    invalid_orders = gold.filter(
        col("total_orders") <= 0
    ).count()

    assert invalid_orders == 0, "FAIL: Invalid daily order counts"
    print("PASS: All daily order counts are positive")

    # 5. Sales and freight must not be negative
    invalid_amounts = gold.filter(
        (col("total_product_sales") < 0)
        | (col("total_freight") < 0)
        | (col("total_sales") < 0)
    ).count()

    assert invalid_amounts == 0, "FAIL: Negative sales values found"
    print("PASS: No negative sales or freight values")

    # 6. Total sales must equal product sales + freight
    inconsistent_sales = gold.filter(
        spark_abs(
            col("total_sales")
            - col("total_product_sales")
            - col("total_freight")
        ) > 0.011
    ).count()

    assert inconsistent_sales == 0, "FAIL: Sales totals do not match"
    print("PASS: Total sales equals product sales plus freight")

    # 7. Daily order counts must reconcile with delivered orders
    delivered_orders = orders.filter(
        col("order_status") == "delivered"
    )

    expected_orders = (
        delivered_orders
        .join(items.select("order_id").distinct(), "order_id", "inner")
        .select("order_id")
        .distinct()
        .count()
    )

    actual_orders = gold.agg(
        spark_sum("total_orders").alias("total")
    ).first()["total"]

    assert actual_orders == expected_orders, (
        f"FAIL: Gold order total {actual_orders} "
        f"does not match expected {expected_orders}"
    )
    print(f"PASS: Order counts reconcile ({actual_orders} orders)")

    print("\nALL GOLD DATA QUALITY CHECKS PASSED")

finally:
    spark.stop()

