
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"
SILVER_DIR = PROJECT_ROOT / "data" / "silver"

spark = (
    SparkSession.builder
    .appName("EcommerceSilverPipeline")
    .master("local[*]")
    .config("spark.sql.session.timeZone", "UTC")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


def load_bronze(table_name):
    path = BRONZE_DIR / table_name
    return spark.read.parquet(str(path))


def write_silver(df, table_name):
    output = SILVER_DIR / table_name
    df.write.mode("overwrite").parquet(str(output))


def transform_orders():
    df = load_bronze("orders")

    timestamp_columns = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]

    for column in timestamp_columns:
        df = df.withColumn(
            column,
            F.to_timestamp(F.col(column), "yyyy-MM-dd HH:mm:ss"),
        )

    valid_condition = (
        F.col("order_id").isNotNull()
        & F.col("customer_id").isNotNull()
        & F.col("order_purchase_timestamp").isNotNull()
    )

    valid = df.filter(valid_condition)
    rejected = df.filter(~valid_condition)

    write_silver(valid, "orders")
    write_silver(rejected, "quarantine/orders")

    print("Orders - valid:", valid.count())
    print("Orders - rejected:", rejected.count())


def transform_customers():
    df = load_bronze("customers")

    valid_condition = (
        F.col("customer_id").isNotNull()
        & F.col("customer_unique_id").isNotNull()
    )

    valid = df.filter(valid_condition)
    rejected = df.filter(~valid_condition)

    write_silver(valid, "customers")
    write_silver(rejected, "quarantine/customers")

    print("Customers - valid:", valid.count())
    print("Customers - rejected:", rejected.count())


def transform_order_items():
    df = load_bronze("order_items")

    valid_condition = (
        F.col("order_id").isNotNull()
        & F.col("product_id").isNotNull()
        & F.col("order_item_id").isNotNull()
        & (F.col("price") >= 0)
        & (F.col("freight_value") >= 0)
    )

    valid = df.filter(valid_condition)
    rejected = df.filter(~valid_condition)

    valid = valid.withColumn(
        "shipping_limit_date",
        F.to_timestamp(
            "shipping_limit_date", "yyyy-MM-dd HH:mm:ss"
        ),
    )

    write_silver(valid, "order_items")
    write_silver(rejected, "quarantine/order_items")

    print("Order items - valid:", valid.count())
    print("Order items - rejected:", rejected.count())

def transform_products():
    df = load_bronze("products")

    valid_condition = F.col("product_id").isNotNull()

    valid = df.filter(valid_condition)
    rejected = df.filter(~valid_condition)

    # Clean category text without rejecting products with missing categories.
    valid = valid.withColumn(
        "product_category_name",
        F.trim(F.col("product_category_name")),
    )

    write_silver(valid, "products")
    write_silver(rejected, "quarantine/products")

    print("Products - valid:", valid.count())
    print("Products - rejected:", rejected.count())

def transform_payments():
    df = load_bronze("order_payments")

    valid_condition = (
        F.col("order_id").isNotNull()
        & F.col("payment_sequential").isNotNull()
        & F.col("payment_value").isNotNull()
        & (F.col("payment_value") >= 0)
    )

    valid = df.filter(valid_condition)
    rejected = df.filter(~valid_condition)

    write_silver(valid, "order_payments")
    write_silver(rejected, "quarantine/order_payments")

    print("Payments - valid:", valid.count())
    print("Payments - rejected:", rejected.count())


def main():
    try:
        SILVER_DIR.mkdir(parents=True, exist_ok=True)

        transform_orders()
        transform_customers()
        transform_order_items()
        transform_payments()
        transform_products()

        print("\nSilver transformation completed.")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
