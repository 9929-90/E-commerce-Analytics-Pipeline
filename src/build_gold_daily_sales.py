
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    to_date,
    countDistinct,
    sum as spark_sum,
    round as spark_round,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SILVER_DIR = PROJECT_ROOT / "data" / "silver"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"

spark = (
    SparkSession.builder
    .appName("BuildGoldDailySales")
    .master("local[*]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

try:
    # Read cleaned Silver data
    orders = spark.read.parquet(str(SILVER_DIR / "orders"))
    items = spark.read.parquet(str(SILVER_DIR / "order_items"))

    # Keep delivered orders for the sales report
    delivered_orders = orders.filter(
        col("order_status") == "delivered"
    )

    # Join orders with their items
    sales = delivered_orders.join(
        items,
        on="order_id",
        how="inner",
    )

    # Aggregate sales by order purchase date
    gold_daily_sales = (
        sales
        .withColumn(
            "order_date",
            to_date(col("order_purchase_timestamp")),
        )
        .groupBy("order_date")
        .agg(
            countDistinct("order_id").alias("total_orders"),
            spark_round(
                spark_sum("price"), 2
            ).alias("total_product_sales"),
            spark_round(
                spark_sum("freight_value"), 2
            ).alias("total_freight"),
        )
        .withColumn(
            "total_sales",
            spark_round(
                col("total_product_sales") + col("total_freight"),
                2,
            ),
        )
        .orderBy("order_date")
    )

    output_path = GOLD_DIR / "gold_daily_sales"

    # Write the Gold table in Parquet format
    (
        gold_daily_sales
        .write
        .mode("overwrite")
        .parquet(str(output_path))
    )

    print("\nGold daily sales table created successfully.")
    print(f"Output path: {output_path}")
    print(f"Number of daily records: {gold_daily_sales.count()}")

    print("\nSample records:")
    gold_daily_sales.show(10, truncate=False)

    print("\nGold table schema:")
    gold_daily_sales.printSchema()

finally:
    spark.stop()
