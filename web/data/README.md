# Optional dashboard data

The dashboard automatically requests these files from this folder:

- `daily_sales.csv` — export of `data/gold/gold_daily_sales`
- `product_performance.csv` — export of `data/gold/gold_product_performance`

Generate them after running the pipeline:

```bash
python scripts/export_gold_dashboard.py
```

The CSV files are ignored by Git by default. If you want the hosted GitHub Pages dashboard to load real trends and product metrics automatically, inspect the generated aggregate files and their size/terms, then deliberately publish them:

```bash
git add -f web/data/daily_sales.csv web/data/product_performance.csv
git commit -m "Publish reviewed Gold aggregates for dashboard"
git push
```

Only publish derived aggregates you are comfortable making public. The dashboard can also load local CSVs through its file inputs; those are read in the browser and are not uploaded.
