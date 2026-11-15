from pathlib import Path
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timezone


# ==========================================
# 1. PROJECT PATHS
# ==========================================

def find_project_root():
    current = Path(__file__).resolve().parent

    for folder in [current, *current.parents]:
        if (folder / "sites.py").exists():
            return folder

    raise FileNotFoundError(
        "Could not find sites.py. "
        "Place this script inside the project folder."
    )


PROJECT = find_project_root()

if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from sites import SITES

VISIBILITY_DIR = PROJECT / "results" / "visibility"
GRAPH_DIR = PROJECT / "results" / "graphs"


# ==========================================
# 2. DATA CONVERSION
# ==========================================

def convert_visibility(series):
    text = series.astype("string").str.strip().str.lower()

    result = pd.Series(
        float("nan"),
        index=series.index,
        dtype="float64"
    )

    result[text.isin(
        ["1", "1.0", "true", "yes", "visible"]
    )] = 1

    result[text.isin(
        ["0", "0.0", "false", "no", "blocked", "hidden"]
    )] = 0

    numeric = pd.to_numeric(series, errors="coerce")

    result[numeric == 1] = 1
    result[numeric == 0] = 0

    return result


# ==========================================
# 3. LOAD SELECTED SITE DATA
# ==========================================

def load_site_data(site_id):

    sun_file = VISIBILITY_DIR / f"{site_id}_sun_visibility.csv"
    earth_file = VISIBILITY_DIR / f"{site_id}_earth_visibility.csv"

    if not sun_file.exists():
        raise FileNotFoundError(f"Sun data not found: {sun_file}")

    if not earth_file.exists():
        raise FileNotFoundError(f"Earth data not found: {earth_file}")

    def read_body_file(file_path, body):

        df = pd.read_csv(file_path)

        time_candidates = [
            "datetime_utc",
            "timestamp_utc",
            "datetime",
            "timestamp",
            "date_time",
            "time_utc",
            "time"
        ]

        time_col = next(
            (col for col in time_candidates if col in df.columns),
            None
        )

        if time_col is None:
            raise ValueError(
                f"No time column found in {file_path.name}. "
                f"Columns: {list(df.columns)}"
            )

        visibility_candidates = [
            "visible",
            "is_visible",
            "visibility",
            "body_visible",
            "terrain_visible",
            "visible_flag",
            "visibility_status"
        ]

        visibility_col = next(
            (col for col in visibility_candidates if col in df.columns),
            None
        )

        margin_col = next(
            (
                col for col in df.columns
                if "margin" in col.lower()
                or "clearance" in col.lower()
            ),
            None
        )

        df["_time"] = pd.to_datetime(
            df[time_col],
            errors="coerce",
            utc=True
        )

        if visibility_col is not None:
            df[f"{body}_visible"] = convert_visibility(
                df[visibility_col]
            )

        elif margin_col is not None:
            margin = pd.to_numeric(
                df[margin_col],
                errors="coerce"
            )

            df[f"{body}_visible"] = (margin > 0).astype(float)
            df.loc[margin.isna(), f"{body}_visible"] = float("nan")

        else:
            raise ValueError(
                f"No visibility or margin column found in {file_path.name}. "
                f"Columns: {list(df.columns)}"
            )

        return (
            df[["_time", f"{body}_visible"]]
            .dropna(subset=["_time"])
            .drop_duplicates("_time")
        )

    sun = read_body_file(sun_file, "sun")
    earth = read_body_file(earth_file, "earth")

    df = pd.merge(
        sun,
        earth,
        on="_time",
        how="outer"
    ).sort_values("_time")

    known = (
        df["sun_visible"].notna()
        & df["earth_visible"].notna()
    )

    df["both_visible"] = float("nan")

    df.loc[known, "both_visible"] = (
        (df.loc[known, "sun_visible"] == 1)
        & (df.loc[known, "earth_visible"] == 1)
    ).astype(float)

    return df.reset_index(drop=True)
# ==========================================
def get_tick_interval(total_hours):

    if total_hours <= 48:
        return 3

    elif total_hours <= 96:
        return 6

    elif total_hours <= 336:
        return 12

    return 24
def create_graph(
    df,
    column,
    title,
    output_path
):

    data = df.dropna(
        subset=["_time", column]
    )

    if data.empty:
        raise ValueError(
            f"No valid samples for {title}"
        )

    fig, ax = plt.subplots(figsize=(14, 5))

    ax.step(
        data["_time"],
        data[column],
        where="post",
        linewidth=1.8
    )

    ax.set_title(title)
    ax.set_xlabel("Mission Time (UTC)")
    ax.set_ylabel("Visibility")

    ax.set_yticks([0, 1])
    ax.set_yticklabels([
        "Blocked (0)",
        "Visible (1)"
    ])

    ax.set_ylim(-0.15, 1.15)

    ax.grid(
        True,
        which="major",
        alpha=0.35
    )

    total_hours = (
        data["_time"].max()
        - data["_time"].min()
    ).total_seconds() / 3600

    interval = get_tick_interval(total_hours)

    ax.xaxis.set_major_locator(
        mdates.HourLocator(
            interval=interval,
            tz=timezone.utc
        )
    )

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter(
            "%d %b\n%H:%M",
            tz=timezone.utc
        )
    )
    fig.tight_layout()

    fig.savefig(
        output_path,
        dpi=180,
        bbox_inches="tight"
    )

    plt.close(fig)


# ==========================================
# 6. GENERATE GRAPHS FOR ONE SITE ONLY
# ==========================================

def generate_site_graphs(site_id):

    if site_id not in SITES:
        raise ValueError(
            f"Unknown site: {site_id}"
        )

    df = load_site_data(site_id)

    site_name = SITES[site_id]["name"]

    output_folder = GRAPH_DIR / site_id
    output_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    create_graph(
        df,
        "sun_visible",
        f"{site_id} - {site_name}: Sun Visibility",
        output_folder / "sun_visibility.png"
    )

    create_graph(
        df,
        "earth_visible",
        f"{site_id} - {site_name}: Earth Visibility",
        output_folder / "earth_visibility.png"
    )

    create_graph(
        df,
        "both_visible",
        f"{site_id} - {site_name}: Simultaneous Visibility",
        output_folder / "both_visibility.png"
    )

    print("\nGraphs generated successfully.")
    print(f"Selected site: {site_id}")
    print(f"Output folder: {output_folder}")


# ==========================================
# 7. TEMPORARY COMMAND-LINE TEST
# ==========================================

if __name__ == "__main__":

    print("\n===== LUNAR MISSION GRAPH GENERATOR =====")

    print("\nAvailable sites:")

    for site_id, data in SITES.items():
        print(f"{site_id}: {data['name']}")

    selected_site = input(
        "\nEnter selected site ID: "
    ).strip()

    try:
        generate_site_graphs(selected_site)

    except Exception as error:
        print("\nERROR:", error)

