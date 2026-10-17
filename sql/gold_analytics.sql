
-- 1. Daily sales summary
SELECT
    order_date,
    total_orders,
    ROUND(total_product_sales, 2) AS product_sales,
    ROUND(total_freight, 2) AS freight_revenue,
    ROUND(total_sales, 2) AS total_sales
FROM read_parquet('data/gold/gold_daily_sales/**/*.parquet')
ORDER BY order_date;


-- 2. Top 10 products by revenue
SELECT
    product_id,
    product_category_name,
    units_sold,
    total_orders,
    ROUND(product_revenue, 2) AS product_revenue,
    ROUND(total_revenue, 2) AS total_revenue
FROM read_parquet('data/gold/gold_product_performance/**/*.parquet')
ORDER BY product_revenue DESC
LIMIT 10;


-- 3. Revenue by product category
SELECT
    COALESCE(product_category_name, 'unknown') AS category,
    SUM(units_sold) AS units_sold,
    SUM(total_orders) AS product_order_count,
    ROUND(SUM(product_revenue), 2) AS product_revenue,
    ROUND(SUM(freight_revenue), 2) AS freight_revenue,
    ROUND(SUM(total_revenue), 2) AS total_revenue
FROM read_parquet('data/gold/gold_product_performance/**/*.parquet')
GROUP BY COALESCE(product_category_name, 'unknown')
ORDER BY total_revenue DESC
LIMIT 15;


-- 4. Products that have never been sold
SELECT
    COUNT(*) AS unsold_product_count
FROM read_parquet('data/gold/gold_product_performance/**/*.parquet')
WHERE units_sold = 0;


-- 5. Overall product performance
SELECT
    COUNT(*) AS total_products,
    SUM(units_sold) AS total_units_sold,
    ROUND(SUM(product_revenue), 2) AS total_product_revenue,
    ROUND(SUM(freight_revenue), 2) AS total_freight_revenue,
    ROUND(SUM(total_revenue), 2) AS total_revenue
FROM read_parquet('data/gold/gold_product_performance/**/*.parquet');


-- 6. Rank product categories by total revenue
WITH category_revenue AS (
    SELECT
        COALESCE(product_category_name, 'unknown') AS category,
        SUM(product_revenue) AS revenue
    FROM read_parquet(
        'data/gold/gold_product_performance/**/*.parquet'
    )
    GROUP BY COALESCE(product_category_name, 'unknown')
),
ranked_categories AS (
    SELECT
        category,
        ROUND(revenue, 2) AS revenue,
        DENSE_RANK() OVER (
            ORDER BY revenue DESC
        ) AS revenue_rank
    FROM category_revenue
)
SELECT *
FROM ranked_categories
ORDER BY revenue_rank
LIMIT 10;


-- 7. Calculate each category's share of total revenue
WITH category_revenue AS (
    SELECT
        COALESCE(product_category_name, 'unknown') AS category,
        SUM(product_revenue) AS revenue
    FROM read_parquet(
        'data/gold/gold_product_performance/**/*.parquet'
    )
    GROUP BY COALESCE(product_category_name, 'unknown')
)
SELECT
    category,
    ROUND(revenue, 2) AS revenue,
    ROUND(
        100.0 * revenue / SUM(revenue) OVER (),
        2
    ) AS revenue_percentage
FROM category_revenue
ORDER BY revenue DESC
LIMIT 10;


-- 8. Compare each day's sales with the previous recorded day
WITH daily_changes AS (
    SELECT
        order_date,
        total_orders,
        total_sales,
        LAG(total_sales) OVER (
            ORDER BY order_date
        ) AS previous_day_sales
    FROM read_parquet(
        'data/gold/gold_daily_sales/**/*.parquet'
    )
)
SELECT
    order_date,
    total_orders,
    ROUND(total_sales, 2) AS total_sales,
    ROUND(previous_day_sales, 2) AS previous_day_sales,
    ROUND(total_sales - previous_day_sales, 2) AS sales_change
FROM daily_changes
ORDER BY order_date DESC
LIMIT 10;


-- 9. Product-level conditional aggregation
SELECT
    COUNT(*) AS total_products,
    SUM(CASE WHEN units_sold > 0 THEN 1 ELSE 0 END) AS sold_products,
    SUM(CASE WHEN units_sold = 0 THEN 1 ELSE 0 END) AS unsold_products,
    ROUND(AVG(product_revenue), 2) AS avg_product_revenue
FROM read_parquet(
    'data/gold/gold_product_performance/**/*.parquet'
);
