
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def load_csv(filename):
    path = RAW_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    return pd.read_csv(path)


def check_unique_key(df, columns, table_name):
    duplicates = df.duplicated(subset=columns).sum()

    print(
        f"{table_name} | Key {columns} | "
        f"Duplicate keys: {duplicates:,}"
    )


def main():
    orders = load_csv("olist_orders_dataset.csv")
    items = load_csv("olist_order_items_dataset.csv")
    customers = load_csv("olist_customers_dataset.csv")
    payments = load_csv("olist_order_payments_dataset.csv")

    print("\n========== 1. PRIMARY KEY CHECKS ==========")

    check_unique_key(orders, ["order_id"], "Orders")
    check_unique_key(customers, ["customer_id"], "Customers")
    check_unique_key(
        items, ["order_id", "order_item_id"], "Order items"
    )
    check_unique_key(
        payments, ["order_id", "payment_sequential"], "Payments"
    )

    print("\n========== 2. REFERENTIAL INTEGRITY ==========")

    order_ids = set(orders["order_id"])
    customer_ids = set(customers["customer_id"])

    missing_customers = (~orders["customer_id"].isin(customer_ids)).sum()
    missing_item_orders = (~items["order_id"].isin(order_ids)).sum()
    missing_payment_orders = (~payments["order_id"].isin(order_ids)).sum()

    print("Orders without matching customers:", missing_customers)
    print("Items without matching orders:", missing_item_orders)
    print("Payments without matching orders:", missing_payment_orders)

    print("\n========== 3. ORDER STATUS ANALYSIS ==========")

    print(orders["order_status"].value_counts(dropna=False).to_string())

    print("\nMissing delivery dates by order status:")

    missing_by_status = (
        orders.assign(
            delivery_date_missing=orders[
                "order_delivered_customer_date"
            ].isna()
        )
        .groupby("order_status")["delivery_date_missing"]
        .agg(["sum", "count"])
    )

    print(missing_by_status.to_string())

    print("\n========== 4. BUSINESS DATA CHECKS ==========")

    print("Orders:", len(orders))
    print("Order items:", len(items))
    print("Customers:", len(customers))
    print("Payment records:", len(payments))

    print("Orders with non-positive item prices:",
          (items["price"] <= 0).sum())

    print("Orders with negative freight values:",
          (items["freight_value"] < 0).sum())

    print("Payments with negative values:",
          (payments["payment_value"] < 0).sum())

    print("\n========== VALIDATION COMPLETE ==========")


if __name__ == "__main__":
    main()
