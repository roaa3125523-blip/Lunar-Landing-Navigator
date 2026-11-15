from pathlib import Path
from datetime import datetime, time
from flask import Flask, request, jsonify, send_from_directory

from sites import SITES
from visibility import calculate_visibility, compare_all_sites

PROJECT = Path(__file__).resolve().parent

app = Flask(__name__, static_folder=None)


def parse_date(value, end_of_day=False):
    try:
        date_value = datetime.strptime(value, "%Y-%m-%d").date()
        selected_time = time(23, 0) if end_of_day else time(0, 0)
        return datetime.combine(date_value, selected_time)
    except (TypeError, ValueError):
        raise ValueError("Dates must use YYYY-MM-DD format.")


@app.get("/")
def home():
    return send_from_directory(PROJECT, "index.html")


@app.get("/api/sites")
def get_sites():
    return jsonify([
        {"site_id": site_id, "site_name": data["name"]}
        for site_id, data in SITES.items()
    ])


@app.post("/api/analysis")
def analyze_mission():
    try:
        data = request.get_json(silent=True) or {}

        site_id = data.get("site_id")
        if site_id not in SITES:
            return jsonify({"error": "Please select a valid landing site."}), 400

        start_val = data.get("start_date") or data.get("startDate")
        end_val = data.get("end_date") or data.get("endDate")
        start_time = parse_date(start_val)
        end_time = parse_date(end_val, end_of_day=True)

        if end_time <= start_time:
            return jsonify({"error": "End date must be after start date."}), 400

        result = calculate_visibility(site_id, start_time, end_time)

        hourly_results = []
        for row in result["rows"]:
            hourly_results.append({
                "time": row["timestamp"].isoformat(sep=" "),
                "sun_visibility": (
                    bool(row["sun_visible"])
                    if row["sun_visible"] is not None else None
                ),
                "earth_visibility": (
                    bool(row["earth_visible"])
                    if row["earth_visible"] is not None else None
                ),
                "simultaneous_visibility": (
                    bool(row["both_visible"])
                    if row["both_visible"] is not None else None
                ),
                "sun_margin_deg": row["sun_margin_deg"],
                "earth_margin_deg": row["earth_margin_deg"],
            })

        return jsonify({
            "site_id": site_id,
            "site_name": SITES[site_id]["name"],
            "hourly_results": hourly_results,
            "summary": result["summary"],
        })

    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except FileNotFoundError as error:
        return jsonify({
            "error": "Required project data file is missing.",
            "details": str(error),
        }), 500
    except Exception as error:
        app.logger.exception("Analysis failed")
        return jsonify({
            "error": "Analysis failed.",
            "details": str(error),
        }), 500


@app.post("/api/recommendations")
def recommend_sites():
    try:
        data = request.get_json(silent=True) or {}

        start_val = data.get("start_date") or data.get("startDate")
        end_val = data.get("end_date") or data.get("endDate")

        start_time = parse_date(start_val)
        end_time = parse_date(end_val, end_of_day=True)

        if end_time <= start_time:
            return jsonify({"error": "End date must be after start date."}), 400

        priority = data.get("priority", "")
        reqs = data.get("requirements") or {}

        require_sun = bool(
            data.get("requireSun") or
            reqs.get("sun_visibility") or
            priority == "sun"
        )
        require_earth = bool(
            data.get("requireEarth") or
            reqs.get("earth_visibility") or
            priority == "earth"
        )
        require_both = bool(
            data.get("requireBoth") or
            reqs.get("simultaneous_visibility") or
            priority == "both"
        )

        if require_both or (require_sun and require_earth):
            metric = "both"
            label = "simultaneous Sun and Earth visibility"
        elif require_earth:
            metric = "earth"
            label = "Earth visibility"
        else:
            metric = "sun"
            label = "Sun visibility"

        summaries = compare_all_sites(start_time, end_time)

        ranked = sorted(
            summaries,
            key=lambda item: item.get(metric, {}).get("visible_hours", 0),
            reverse=True,
        )

        recommendations = []

        for item in ranked:
            hours = item.get(metric, {}).get("visible_hours", 0)
            longest = item.get(metric, {}).get("longest_continuous_hours", 0)

            recommendations.append({
                "site_id": item["site_id"],
                "site_name": item["site_name"],
                "visible_hours": hours,
                "longest_continuous_hours": longest,
                "reason": (
                    f"{hours} estimated hours of {label}; "
                    f"longest continuous interval: {longest} hours."
                ),
                "summary": item,
            })

        return jsonify({
            "recommendations": recommendations,
        })

    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except FileNotFoundError as error:
        return jsonify({
            "error": "Required project data file is missing.",
            "details": str(error),
        }), 500
    except Exception as error:
        app.logger.exception("Recommendation failed")
        return jsonify({
            "error": "Recommendation failed.",
            "details": str(error),
        }), 500


@app.route("/<path:filename>")
def project_files(filename):
    return send_from_directory(PROJECT, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)