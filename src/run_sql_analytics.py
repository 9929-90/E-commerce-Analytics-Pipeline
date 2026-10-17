
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SQL_FILE = PROJECT_ROOT / "sql" / "gold_analytics.sql"

con = duckdb.connect(database=":memory:")

try:
    sql_text = SQL_FILE.read_text(encoding="utf-8")

    # Execute each semicolon-separated SQL query.
    queries = [
        query.strip()
        for query in sql_text.split(";")
        if query.strip()
    ]

    for index, query in enumerate(queries, start=1):
        print(f"\n{'=' * 70}")
        print(f"QUERY {index}")
        print("=" * 70)

        result = con.execute(query)
        print(result.df().to_string(index=False))

    print("\nSQL analytics completed successfully.")

finally:
    con.close()
