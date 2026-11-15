import csv
import json
from pathlib import Path
from datetime import datetime, timezone

from sites import SITES


PROJECT = Path(__file__).resolve().parent
DATA_DIR = PROJECT / "results" / "visibility"
OUTPUT_FILE = DATA_DIR / "top_3_sites.json"


def parse_user_date(value):
    dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def parse_timestamp(value):
    dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))

    if dt.tzinfo is None:
        raise ValueError("CSV timestamp has no timezone.")

    return dt.astimezone(timezone.utc)


def find_column(headers, candidates):
    columns = {h.strip().lower(): h for h in headers}

    for name in candidates:
        if name in columns:
            return columns[name]

    return None


def read_visibility(site_id, body, start, end):

    path = DATA_DIR / f"{site_id}_{body}_visibility.csv"

    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames:
            raise ValueError(f"Empty CSV: {path.name}")

        time_col = find_column(
            reader.fieldnames,
            [
                "datetime_utc", "timestamp_utc", "datetime",
                "timestamp", "date_time", "time_utc", "time"
            ]
        )

        visible_col = find_column(
            reader.fieldnames,
            [
                "visible", "is_visible", "visibility",
                "body_visible", "terrain_visible",
                "visible_flag", "visibility_status"
            ]
        )

        margin_col = next(
            (
                h for h in reader.fieldnames
                if "margin" in h.lower() or "clearance" in h.lower()
            ),
            None
        )

        if time_col is None:
            raise ValueError(f"No time column in {path.name}")

        if visible_col is None and margin_col is None:
            raise ValueError(
                f"No visibility or margin column in {path.name}"
            )

        data = {}

        for row in reader:
            raw_time = row.get(time_col, "").strip()

            if not raw_time:
                continue

            timestamp = parse_timestamp(raw_time)

            if start <= timestamp <= end:

                if visible_col is not None:
                    raw = row.get(visible_col, "").strip().lower()

                    if raw in ("1", "1.0", "true", "yes", "visible", "open"):
                        visible = 1
                    elif raw in ("0", "0.0", "false", "no", "blocked", "hidden"):
                        visible = 0
                    else:
                        visible = None

                else:
                    raw = row.get(margin_col, "").strip()

                    try:
                        visible = 1 if float(raw) > 0 else 0
                    except (ValueError, TypeError):
                        visible = None

                if timestamp in data:
                    raise ValueError(
                        f"Duplicate timestamp in {path.name}: {timestamp}"
                    )

                data[timestamp] = visible

    return data


def calculate_hours(data):

    times = sorted(data)

    if len(times) < 2:
        raise ValueError("Not enough samples in selected mission period.")

    hours = 0.0

    for i in range(len(times) - 1):

        t1 = times[i]
        t2 = times[i + 1]

        interval = (t2 - t1).total_seconds() / 3600

        if interval <= 0:
            raise ValueError("Invalid time interval.")

        if data[t1] == 1 and data[t2] == 1:
            hours += interval

    return hours


def calculate_site(site_id, start, end):

    sun = read_visibility(site_id, "sun", start, end)
    earth = read_visibility(site_id, "earth", start, end)

    if set(sun) != set(earth):
        raise ValueError(
            f"Sun and Earth timestamps do not match for {site_id}"
        )

    both = {
        timestamp: (
            1 if sun[timestamp] == 1 and earth[timestamp] == 1
            else 0 if sun[timestamp] is not None
            and earth[timestamp] is not None
            else None
        )
        for timestamp in sun
    }

    return {
        "site": site_id,
        "sun_hours": round(calculate_hours(sun), 3),
        "earth_hours": round(calculate_hours(earth), 3),
        "both_hours": round(calculate_hours(both), 3)
    }


def main():

    print("\nLUNAR MISSION SITE RECOMMENDER")

    print("\nEnter mission dates in UTC.")
    print("Format: YYYY-MM-DD HH:MM")
    print("Example: 2026-11-10 00:00")

    start = parse_user_date(
        input("\nMission start: ")
    )

    end = parse_user_date(
        input("Mission end: ")
    )

    if end <= start:
        print("ERROR: End date must be after start date.")
        return

    print("\nChoose mission objective:")
    print("1 - Sun Visibility")
    print("2 - Earth Visibility")
    print("3 - Both Visible Simultaneously")

    choice = input("\nYour choice: ").strip()

    objectives = {
        "1": "sun_hours",
        "2": "earth_hours",
        "3": "both_hours"
    }

    if choice not in objectives:
        print("Invalid objective.")
        return

    objective = objectives[choice]

    results = []
    errors = []

    for site_id in SITES:

        try:
            result = calculate_site(site_id, start, end)
            results.append(result)

        except Exception as error:
            errors.append({
                "site": site_id,
                "error": str(error)
            })

    if errors:
        print("\nSome sites could not be compared:")
        for item in errors:
            print(item["site"], "-", item["error"])

        print("\nRanking stopped to avoid comparing incomplete data.")
        return

    ranked = sorted(
        results,
        key=lambda item: item[objective],
        reverse=True
    )

    top_three = ranked[:3]

    output = {
        "mission_start_utc": start.isoformat(),
        "mission_end_utc": end.isoformat(),
        "objective": objective,
        "top_3_sites": top_three,
        "all_sites": ranked
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    print("\nTOP 3 RECOMMENDED SITES\n")

    for i, site in enumerate(top_three, 1):
        print(
            f"{i}. {site['site']} "
            f"- {site[objective]} hours"
        )

    print("\nSaved to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()