
from pathlib import Path
import subprocess
import sys
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PIPELINE_STEPS = [
    ("Bronze ingestion", "src/ingest_bronze.py"),
    ("Silver transformations", "src/transform_silver.py"),
    ("Silver data validation", "src/validate_data.py"),
    ("Build Gold daily sales", "src/build_gold_daily_sales.py"),
    ("Validate Gold daily sales", "src/validate_gold_daily_sales.py"),
    ("Build Gold product performance", "src/build_gold_product_performance.py"),
    ("Validate Gold product performance", "src/validate_gold_product_performance.py"),
    ("Run SQL analytics", "src/run_sql_analytics.py"),
]


def main():
    start_time = datetime.now()

    print("=" * 60)
    print("E-COMMERCE DATA ENGINEERING PIPELINE")
    print("=" * 60)

    for step_name, script_path in PIPELINE_STEPS:
        full_path = PROJECT_ROOT / script_path

        print(f"\n[{datetime.now():%H:%M:%S}] START: {step_name}")
        print("-" * 60)

        if not full_path.is_file():
            print(f"ERROR: Script not found: {full_path}")
            sys.exit(1)

        result = subprocess.run(
            [sys.executable, str(full_path)],
            cwd=str(PROJECT_ROOT),
            check=False,
        )

        if result.returncode != 0:
            print(f"\nFAILED: {step_name}")
            print(f"Exit code: {result.returncode}")
            print("Pipeline stopped to prevent later steps from running.")
            sys.exit(result.returncode)

        print(f"\nSUCCESS: {step_name}")

    duration = (datetime.now() - start_time).total_seconds()

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print(f"Total execution time: {duration:.2f} seconds")
    print("=" * 60)


if __name__ == "__main__":
    main()

