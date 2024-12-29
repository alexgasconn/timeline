from flask import Flask, request, render_template_string
import json
import folium
from folium.plugins import HeatMap
import re
from datetime import datetime, timezone
from geopy.distance import geodesic

app = Flask(__name__)

# File path to the JSON
file_path = r"C:\\Users\\usuario\\OneDrive\\Escritorio\\VS files\\timeline\\timeline.json"

# Helper function to extract latitude and longitude from the 'latLng' field
def parse_lat_lng(lat_lng_str):
    match = re.match(r"([-+]?\d*\.\d+|\d+)\u00b0,\s*([-+]?\d*\.\d+|\d+)\u00b0", lat_lng_str)
    if match:
        return float(match.group(1)), float(match.group(2))
    return None

# Helper function to filter segments by provided criteria and calculate statistics
def filter_segments(data, start_time, end_time, confidence_level=None, semantic_type=None):
    # Define probability ranges for confidence levels
    confidence_ranges = {
        "high": (0.0, 1.0),
        "medium": (0.0, 0.8),
        "low": (0.0, 0.5),
    }
    filtered_locations = []
    total_distance = 0.0  # Total distance covered (in meters)
    total_time = 0.0  # Total time spent (in seconds)
    visit_count = 0  # Total number of visits

    for segment in data.get("semanticSegments", []):
        segment_start = datetime.fromisoformat(segment["startTime"].replace("Z", "+00:00"))
        segment_end = datetime.fromisoformat(segment["endTime"].replace("Z", "+00:00"))

        # Ensure consistent timezone for comparison
        segment_start = segment_start.astimezone(timezone.utc)
        segment_end = segment_end.astimezone(timezone.utc)

        # Time Range Filter
        if not (segment_start.date() >= start_time.date() and segment_end.date() <= end_time.date()):
            continue

        # Confidence Level Filter
        visit_probability = segment.get("visit", {}).get("probability", 0)
        if confidence_level and confidence_level in confidence_ranges:
            prob_min, prob_max = confidence_ranges[confidence_level]
            if not (prob_min <= visit_probability <= prob_max):
                continue

        # Semantic Type Filter
        if semantic_type:
            inferred_type = segment.get("visit", {}).get("topCandidate", {}).get("semanticType", "")
            if inferred_type != semantic_type:
                continue

        # Add valid locations to the list
        if "visit" in segment:
            lat_lng_str = segment["visit"].get("topCandidate", {}).get("placeLocation", {}).get("latLng")
            if lat_lng_str:
                location = parse_lat_lng(lat_lng_str)
                if location:
                    filtered_locations.append(location)

        # Calculate segment distance (if path data exists)
        if "timelinePath" in segment:
            path_points = []
            for path in segment.get("timelinePath", []):
                point = path.get("point")
                if point:
                    location = parse_lat_lng(point)
                    if location:
                        path_points.append(location)

            # Compute distances between consecutive points
            for i in range(len(path_points) - 1):
                if path_points[i] and path_points[i + 1]:
                    segment_distance = geodesic(path_points[i], path_points[i + 1]).meters
                    total_distance += segment_distance

        # Accumulate time and visit count
        total_time += (segment_end - segment_start).total_seconds()
        visit_count += 1

    return filtered_locations, visit_count, total_distance, total_time

# Load the JSON file once
with open(file_path, "r", encoding="utf-8") as file:
    data = json.load(file)

@app.route("/", methods=["GET", "POST"])
def map_view():
    # Default date range (entire dataset range)
    default_start_date = "2013-11-01"
    default_end_date = "2014-11-30"

    # Get user input or set defaults
    start_date = request.form.get("startDate", default_start_date)
    end_date = request.form.get("endDate", default_end_date)
    confidence_level = request.form.get("confidenceLevel", None)
    semantic_type = request.form.get("semanticType", None)

    # Heatmap settings
    radius = int(request.form.get("radius", 8))
    blur = int(request.form.get("blur", 12))
    opacity = float(request.form.get("opacity", 0.7))

    # Convert form inputs to appropriate types
    start_time = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
    end_time = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)

    # Filter locations based on user input and calculate stats
    locations, visit_count, total_distance, total_time = filter_segments(data, start_time, end_time, confidence_level, semantic_type)

    # Generate heatmap
    folium_map = folium.Map(location=[41.4039482, 2.1791428], zoom_start=13)
    if locations:
        HeatMap(locations, radius=radius, blur=blur, max_zoom=1, min_opacity=opacity).add_to(folium_map)

    # Render form, stats, and map
    return render_template_string('''
    <style>
        /* General layout */
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            display: flex;
            height: 100vh;
            overflow: hidden;
        }

        /* Permanent Sidebar */
        .sidebar {
            width: 300px;
            background: #f7f7f7;
            border-right: 1px solid #ddd;
            display: flex;
            flex-direction: column;
            padding: 10px;
            overflow-y: auto;
        }

        /* Form and stats layout */
        form, .stats {
            margin-bottom: 20px;
        }

        label {
            font-size: 0.85em;
            margin-bottom: 5px;
            color: #333;
        }

        input, select {
            width: 100%;
            padding: 4px 6px;
            font-size: 0.9em;
            border: 1px solid #ccc;
            border-radius: 4px;
            margin-bottom: 10px;
        }

        button {
            padding: 6px 12px;
            background: #007BFF;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            width: 100%;
            transition: background 0.2s;
        }

        button:hover {
            background: #0056b3;
        }

        .stats-table {
            border: 1px solid #ddd;
            border-collapse: collapse;
            font-size: 0.9em;
            width: 100%;
        }

        .stats-table th, .stats-table td {
            border: 1px solid #ddd;
            padding: 6px 10px;
            text-align: left;
        }

        .stats-table th {
            background-color: #f7f7f7;
            font-weight: bold;
        }

        /* Main map section */
        .map-container {
            flex: 1;
            position: relative;
        }

        h3 {
            margin-bottom: 10px;
            font-size: 1.1em;
        }
    </style>

    <div style="display: flex; width: 100%;">
        <!-- Permanent Sidebar -->
        <div class="sidebar">
            <form method="POST">
                <div>
                    <label for="startDate">Start Date:</label>
                    <input type="date" id="startDate" name="startDate" value="{{ start_date }}">
                </div>
                <div>
                    <label for="endDate">End Date:</label>
                    <input type="date" id="endDate" name="endDate" value="{{ end_date }}">
                </div>
                <div>
                    <label for="confidenceLevel">Confidence Level:</label>
                    <select id="confidenceLevel" name="confidenceLevel">
                        <option value="" {% if not confidence_level %}selected{% endif %}>Any</option>
                        <option value="high" {% if confidence_level == "high" %}selected{% endif %}>High (0%-100%)</option>
                        <option value="medium" {% if confidence_level == "medium" %}selected{% endif %}>Medium (0%-80%)</option>
                        <option value="low" {% if confidence_level == "low" %}selected{% endif %}>Low (0%-50%)</option>
                    </select>
                </div>
                <div>
                    <label for="semanticType">Place Type:</label>
                    <select id="semanticType" name="semanticType">
                        <option value="" {% if not semantic_type %}selected{% endif %}>Any</option>
                        <option value="INFERRED_HOME" {% if semantic_type == "INFERRED_HOME" %}selected{% endif %}>Home</option>
                        <option value="INFERRED_WORK" {% if semantic_type == "INFERRED_WORK" %}selected{% endif %}>Work</option>
                        <option value="INFERRED_OTHER" {% if semantic_type == "INFERRED_OTHER" %}selected{% endif %}>Other</option>
                    </select>
                </div>
                <div>
                    <label for="radius">Radius:</label>
                    <input type="number" id="radius" name="radius" value="{{ radius }}">
                </div>
                <div>
                    <label for="blur">Blur:</label>
                    <input type="number" id="blur" name="blur" value="{{ blur }}">
                </div>
                <div>
                    <label for="opacity">Opacity:</label>
                    <input type="number" step="0.1" id="opacity" name="opacity" value="{{ opacity }}">
                </div>
                <button type="submit">Filter</button>
            </form>

            <!-- Statistics -->
            <div>
                <h3>Statistics</h3>
                <table class="stats-table">
                    <tr>
                        <th>Total Visits</th>
                        <td>{{ visit_count }}</td>
                    </tr>
                    <tr>
                        <th>Total Distance (km)</th>
                        <td>{{ total_distance / 1000 | round(2) }}</td>
                    </tr>
                    <tr>
                        <th>Total Time (hours)</th>
                        <td>{{ total_time / 3600 | round(2) }}</td>
                    </tr>
                </table>
            </div>
        </div>

        <!-- Map Section -->
        <div class="map-container">
            {{ map_html|safe }}
        </div>
    </div>
'''

, 
        map_html=folium_map._repr_html_(),
        start_date=start_time.date().isoformat() if start_time else "",
        end_date=end_time.date().isoformat() if end_time else "",
        confidence_level=confidence_level if confidence_level else "",
        semantic_type=semantic_type if semantic_type else "",
        radius=radius,
        blur=blur,
        opacity=opacity,
        visit_count=visit_count,
        total_distance=total_distance,
        total_time=total_time)

if __name__ == "__main__":
    app.run(debug=True)

