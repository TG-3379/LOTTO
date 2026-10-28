"""smok95/lotto 의 all.json 을 받아 data/lotto_history.csv 로 변환한다."""
import csv
import json
import urllib.request
from pathlib import Path

URL = "https://smok95.github.io/lotto/results/all.json"
DATA = Path(__file__).parent / "data"


def main():
    DATA.mkdir(exist_ok=True)
    with urllib.request.urlopen(URL, timeout=60) as r:
        rows = json.load(r)
    with open(DATA / "lotto_history.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["draw_no", "date", "n1", "n2", "n3", "n4", "n5", "n6", "bonus"])
        for d in sorted(rows, key=lambda x: x["draw_no"]):
            w.writerow([d["draw_no"], d["date"][:10], *sorted(d["numbers"]), d["bonus_no"]])
    print(f"저장: {len(rows)}회차 -> {DATA / 'lotto_history.csv'}")


if __name__ == "__main__":
    main()
