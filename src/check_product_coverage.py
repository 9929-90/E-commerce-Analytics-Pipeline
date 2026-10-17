
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "data" / "silver" / "products"
ITEMS = ROOT / "data" / "silver" / "order_items"

con = duckdb.connect(":memory:")

try:
    products_path = str(PRODUCTS / "*.parquet")
    items_path = str(ITEMS / "*.parquet")

    query = """
        WITH catalog AS (
            SELECT DISTINCT product_id
            FROM read_parquet(?)
        ),
        sold AS (
            SELECT DISTINCT product_id
            FROM read_parquet(?)
            WHERE product_id IS NOT NULL
        )
        SELECT
            (SELECT COUNT(*) FROM catalog)
                AS catalog_products,
            (SELECT COUNT(*) FROM sold)
                AS distinct_sold_products,
            (
                SELECT COUNT(*)
                FROM catalog c
                LEFT JOIN sold s USING (product_id)
                WHERE s.product_id IS NULL
            ) AS products_without_sales,
            (
                SELECT COUNT(*)
                FROM sold s
                LEFT JOIN catalog c USING (product_id)
                WHERE c.product_id IS NULL
            ) AS sold_products_missing_from_catalog
    """

    result = con.execute(
        query, [products_path, items_path]
    ).fetchdf()

    print("PRODUCT COVERAGE REPORT")
    print("=" * 50)
    print(result.to_string(index=False))

finally:
    con.close()

