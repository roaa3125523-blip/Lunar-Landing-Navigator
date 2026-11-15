import calendar
import requests
from pathlib import Path

from sites import get_east_longitude


API_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

BODIES = {
    "Sun": "10",
    "Earth": "399"
}

BATCH_SIZE = 60


def format_horizons_time(time):
    month = calendar.month_abbr[time.month]

    return (
        f"{time.year}-{month}-{time.day:02d} "
        f"{time.hour:02d}:{time.minute:02d}"
    )


def get_ephemeris(site_id, site_data, body_name, times):

    if body_name not in BODIES:
        raise ValueError(f"Unknown body: {body_name}")

    if not times:
        raise ValueError("The time list is empty.")

    latitude = float(site_data["latitude"])
    longitude = get_east_longitude(
        float(site_data["longitude"])
    )

    # Read the actual site elevation from sites.py
    if "altitude_km" not in site_data:
        raise ValueError(
            f"{site_id} is missing altitude_km in sites.py"
        )

    altitude_km = float(site_data["altitude_km"])

    if not -90 <= latitude <= 90:
        raise ValueError(f"Invalid latitude for {site_id}")

    if not 0 <= longitude <= 360:
        raise ValueError(f"Invalid east longitude for {site_id}")

    all_rows = []
    first_header = None
    last_footer = None

    print(
        f"\nRequesting {body_name} data for {site_id} "
        f"(altitude: {altitude_km} km)..."
    )

    for batch_number, start_index in enumerate(
        range(0, len(times), BATCH_SIZE),
        start=1
    ):

        batch_times = times[
            start_index:start_index + BATCH_SIZE
        ]

        time_list = " ".join(
            f"'{format_horizons_time(t)}'"
            for t in batch_times
        )

        params = {
            "format": "json",
            "COMMAND": BODIES[body_name],
            "OBJ_DATA": "NO",
            "MAKE_EPHEM": "YES",
            "EPHEM_TYPE": "OBSERVER",

            "CENTER": "coord@301",
            "COORD_TYPE": "GEODETIC",

            "SITE_COORD": (
                f"{longitude:.8f},"
                f"{latitude:.8f},"
                f"{altitude_km:.6f}"
            ),

            "TLIST": time_list,
            "TLIST_TYPE": "CAL",
            "TIME_TYPE": "UT",

            "QUANTITIES": "4",
            "ANG_FORMAT": "DEG",
            "APPARENT": "AIRLESS",
            "CSV_FORMAT": "YES"
        }

        print(
            f"  Batch {batch_number}: "
            f"{len(batch_times)} time points"
        )

        response = requests.get(
            API_URL,
            params=params,
            timeout=180
        )

        response.raise_for_status()

        data = response.json()

        if "error" in data:
            raise RuntimeError(data["error"])

        result = data.get("result", "")

        if "$$SOE" not in result or "$$EOE" not in result:
            raise RuntimeError(
                f"Invalid Horizons response for "
                f"{site_id} - {body_name}:\n"
                f"{result[:1500]}"
            )

        header, remaining = result.split("$$SOE", 1)
        table, footer = remaining.split("$$EOE", 1)

        if first_header is None:
            first_header = header

        last_footer = footer

        rows = [
            line.strip()
            for line in table.strip().splitlines()
            if line.strip()
        ]

        all_rows.extend(rows)

    combined_result = (
        first_header
        + "$$SOE\n"
        + "\n".join(all_rows)
        + "\n$$EOE"
        + last_footer
    )

    project_folder = Path(__file__).resolve().parent
    output_folder = project_folder / "results" / site_id
    output_folder.mkdir(parents=True, exist_ok=True)

    output_file = output_folder / f"{body_name.lower()}.txt"

    output_file.write_text(
        combined_result,
        encoding="utf-8"
    )

    print(f"Saved: {output_file}")
    print(f"Total time points: {len(all_rows)}")

    return output_file


def calculate_site_ephemeris(site_id, site_data, times):

    print("\n======================================")
    print("SITE:", site_id)
    print("NAME:", site_data["name"])
    print("ALTITUDE:", site_data["altitude_km"], "km")
    print("======================================")

    successful = []
    failed = []

    for body_name in BODIES:

        try:
            output_file = get_ephemeris(
                site_id,
                site_data,
                body_name,
                times
            )

            successful.append(str(output_file))

        except Exception as error:

            print(
                f"ERROR: {site_id} - "
                f"{body_name}: {error}"
            )

            failed.append(body_name)

    return successful, failed