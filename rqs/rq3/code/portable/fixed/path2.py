import csv
from pathlib import Path

def analyze_csv(base_dir: str):

    base_path = Path(base_dir)
    data_dir = base_path / "data"
    output_dir = base_path / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_file = output_dir / "summary.csv"

    all_stats = []

    for csv_file in data_dir.glob("*.csv"):
        print(f"Analyzing {csv_file.name}...")

        with csv_file.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        num_rows = len(rows)
        num_columns = len(reader.fieldnames) if reader.fieldnames else 0
        first_cols = reader.fieldnames if reader.fieldnames else []

        all_stats.append({
            "filename": csv_file.name,
            "rows": num_rows,
            "columns": num_columns,
            "headers": ";".join(first_cols)
        })

    with summary_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "rows", "columns", "headers"])
        writer.writeheader()
        writer.writerows(all_stats)

    print(f"Summary saved in {summary_file}")

analyze_csv("project_data")
