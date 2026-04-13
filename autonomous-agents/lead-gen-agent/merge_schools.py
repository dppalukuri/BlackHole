"""Merge all school CSVs, deduplicate, and produce one clean file."""

import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

OUTPUT_DIR = Path(__file__).parent / "output"

files = [
    OUTPUT_DIR / "private_school_dubai_20260413.csv",
    OUTPUT_DIR / "best_schools_dubai_20260413.csv",
    OUTPUT_DIR / "international_school_dubai_20260413.csv",
]

all_rows = []
seen_names = set()
headers = None

for f in files:
    if not f.exists():
        continue
    with open(f, encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if headers is None:
            headers = reader.fieldnames
        for row in reader:
            name = row.get("name", "").strip().lower()
            if name and name not in seen_names:
                seen_names.add(name)
                all_rows.append(row)

# Sort by lead_score descending
all_rows.sort(key=lambda r: int(r.get("lead_score", 0)), reverse=True)

out_file = OUTPUT_DIR / "dubai_schools_merged_20260413.csv"
with open(out_file, "w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=headers)
    writer.writeheader()
    writer.writerows(all_rows)

print(f"Merged {len(all_rows)} unique schools to {out_file}")
for row in all_rows[:10]:
    print(f"  [{row['lead_score']}] {row['name']} | {row.get('email', '')} | {row.get('phone', '')}")
