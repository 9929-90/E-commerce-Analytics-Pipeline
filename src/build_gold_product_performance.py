from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

ROOT = Path(__file__).resolve().parent.parent
SILVER = ROOT / "data" / "silver"
GOLD = ROOT / "data" / "gold"
OUTPUT = GOLD / "gold_product_performance"

spark = (
    SparkSession.builder
    .appName("GoldProductPerformance")
    .master("local[*]")
    .config("spark.sql.session.timeZone", "UTC")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


try:
    print("Loading Silver tables...")

    items = spark.read.parquet(str(SILVER / "order_items"))
    products = spark.read.parquet(str(SILVER / "products"))

    print("Order item rows:", items.count())
    print("Product rows:", products.count())

    print("Joining products with order items...")

    joined = products.join(items, on="product_id", how="left")

    print("Aggregating product metrics...")

    gold = (
        joined
        .groupBy("product_id", "product_category_name")
        .agg(
            F.count("order_item_id").alias("units_sold"),
            F.countDistinct("order_id").alias("total_orders"),
            F.coalesce(
                F.sum("price"), F.lit(0.0)
            ).alias("product_revenue"),
            F.coalesce(
                F.sum("freight_value"), F.lit(0.0)
            ).alias("freight_revenue"),
        )
        .withColumn(
            "total_revenue",
            F.col("product_revenue") + F.col("freight_revenue"),
        )
    )

    GOLD.mkdir(parents=True, exist_ok=True)
    gold.write.mode("overwrite").parquet(str(OUTPUT))

    result = spark.read.parquet(str(OUTPUT))

    print("\nGold product performance created successfully!")
    print("Gold product rows:", result.count())
    print("Output path:", OUTPUT)

    print("\nTop 10 products by product revenue:")
    result.orderBy(
        F.desc("product_revenue")
    ).show(10, truncate=False)

    print("\nGold schema:")
    result.printSchema()

finally:
    spark.stop()
