#!/usr/bin/env python3
"""
Utility script for sleep-coach data management.

Usage:
  python data_utils.py init                     — Create data.tab with headers if missing
  python data_utils.py append <json_string>     — Validate and append a row
  python data_utils.py summary [--days N]       — Print a trend summary (default last 7 days)
  python data_utils.py streak                   — Print current streak info
"""

import sys
import os
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

DATA_FILE = "data.tab"
COACH_LOGS_DIR = "coach_logs"

HEADERS = [
    "date", "target_bedtime", "actual_bedtime", "minutes_from_target",
    "wind_down_started", "screen_off_time", "sleep_quality_1to5",
    "energy_next_morning_1to5", "wins", "obstacles", "coach_notes"
]

HEADER_LINE = "\t".join(HEADERS)


def init():
    """Create data.tab and coach_logs/ if they don't exist."""
    os.makedirs(COACH_LOGS_DIR, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            f.write(HEADER_LINE + "\n")
        print(f"Created {DATA_FILE} with headers.")
    else:
        print(f"{DATA_FILE} already exists.")
    print(f"Ensured {COACH_LOGS_DIR}/ exists.")


def validate_time(value):
    """Check HH:MM format or N/A."""
    if value == "N/A":
        return True
    return bool(re.match(r"^\d{2}:\d{2}$", value))


def validate_row(row: dict) -> list:
    """Validate a data row. Returns list of error messages (empty = valid)."""
    errors = []
    # Check all fields present
    for h in HEADERS:
        if h not in row:
            errors.append(f"Missing field: {h}")

    if errors:
        return errors

    # Date format
    try:
        datetime.strptime(row["date"], "%Y-%m-%d")
    except ValueError:
        errors.append(f"Invalid date format: {row['date']} (expected YYYY-MM-DD)")

    # Time fields
    for field in ["target_bedtime", "actual_bedtime", "screen_off_time"]:
        if not validate_time(row.get(field, "")):
            errors.append(f"Invalid time format for {field}: {row[field]} (expected HH:MM or N/A)")

    # Numeric fields
    try:
        int(row["minutes_from_target"])
    except (ValueError, TypeError):
        if row["minutes_from_target"] != "N/A":
            errors.append(f"minutes_from_target must be an integer: {row['minutes_from_target']}")

    for field in ["sleep_quality_1to5", "energy_next_morning_1to5"]:
        val = row.get(field, "")
        if val != "N/A":
            try:
                n = int(val)
                if not 1 <= n <= 5:
                    errors.append(f"{field} must be 1-5, got {n}")
            except (ValueError, TypeError):
                errors.append(f"{field} must be an integer 1-5 or N/A: {val}")

    # yes/no field
    if row.get("wind_down_started", "").lower() not in ("yes", "no", "n/a"):
        errors.append(f"wind_down_started must be yes/no/N/A: {row['wind_down_started']}")

    return errors


def check_duplicate(date_str: str) -> bool:
    """Check if this date already exists as the last row."""
    if not os.path.exists(DATA_FILE):
        return False
    with open(DATA_FILE, "r") as f:
        lines = f.read().strip().split("\n")
    if len(lines) <= 1:
        return False
    last_row = lines[-1].split("\t")
    return last_row[0] == date_str


def append_row(json_string: str):
    """Validate and append a row from JSON string."""
    try:
        row = json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    errors = validate_row(row)
    if errors:
        print("VALIDATION ERRORS:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)

    if check_duplicate(row["date"]):
        print(f"WARNING: Date {row['date']} matches the last row. Skipping to prevent duplicate.", file=sys.stderr)
        sys.exit(2)

    values = [str(row.get(h, "N/A")) for h in HEADERS]
    line = "\t".join(values)

    with open(DATA_FILE, "a") as f:
        f.write(line + "\n")

    print(f"OK: Appended row for {row['date']}")


def load_data() -> list:
    """Load all data rows as list of dicts."""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        lines = f.read().strip().split("\n")
    if len(lines) <= 1:
        return []
    rows = []
    for line in lines[1:]:
        fields = line.split("\t")
        if len(fields) == len(HEADERS):
            rows.append(dict(zip(HEADERS, fields)))
    return rows


def summary(days=7):
    """Print a trend summary of the last N sessions."""
    rows = load_data()
    if not rows:
        print("No data yet.")
        return

    recent = rows[-days:]
    print(f"=== Last {len(recent)} sessions (of {len(rows)} total) ===\n")

    # Target bedtime
    print(f"Current target: {recent[-1]['target_bedtime']}")

    # Actual bedtimes
    actuals = []
    for r in recent:
        if r["actual_bedtime"] != "N/A":
            actuals.append(r["actual_bedtime"])
    if actuals:
        print(f"Actual bedtimes: {', '.join(actuals)}")

    # Minutes from target trend
    deltas = []
    for r in recent:
        try:
            deltas.append(int(r["minutes_from_target"]))
        except (ValueError, TypeError):
            pass

    if len(deltas) >= 2:
        first_half = sum(deltas[:len(deltas)//2]) / (len(deltas)//2)
        second_half = sum(deltas[len(deltas)//2:]) / (len(deltas) - len(deltas)//2)
        if second_half < first_half - 5:
            trend = "IMPROVING (getting closer to target)"
        elif second_half > first_half + 5:
            trend = "REGRESSING (drifting from target)"
        else:
            trend = "STABLE"
        print(f"Trend: {trend} (avg delta: {first_half:.0f} min → {second_half:.0f} min)")

    # Obstacles
    obstacles = [r["obstacles"] for r in recent if r["obstacles"] not in ("N/A", "", "none")]
    if obstacles:
        print(f"\nRecent obstacles: {'; '.join(obstacles[-3:])}")

    # Wins
    wins = [r["wins"] for r in recent if r["wins"] not in ("N/A", "", "none")]
    if wins:
        print(f"Recent wins: {'; '.join(wins[-3:])}")

    # Sleep quality average
    quals = []
    for r in recent:
        try:
            quals.append(int(r["sleep_quality_1to5"]))
        except (ValueError, TypeError):
            pass
    if quals:
        print(f"Avg sleep quality: {sum(quals)/len(quals):.1f}/5")


def streak():
    """Calculate current streak (days within 15 min of target)."""
    rows = load_data()
    if not rows:
        print("No data yet. Streak: 0")
        return

    count = 0
    for r in reversed(rows):
        try:
            delta = abs(int(r["minutes_from_target"]))
            if delta <= 15:
                count += 1
            else:
                break
        except (ValueError, TypeError):
            break

    print(f"Current streak: {count} session(s) within 15 min of target")
    print(f"Total sessions: {len(rows)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "init":
        init()
    elif cmd == "append":
        if len(sys.argv) < 3:
            print("Usage: python data_utils.py append '<json_string>'", file=sys.stderr)
            sys.exit(1)
        append_row(sys.argv[2])
    elif cmd == "summary":
        days = 7
        if len(sys.argv) >= 4 and sys.argv[2] == "--days":
            days = int(sys.argv[3])
        summary(days)
    elif cmd == "streak":
        streak()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)
