# Google Timeline Heatmap

This project visualizes Google Timeline data as a heatmap using Python and Folium. It allows users to extract their location data from Google Timeline and create an interactive map to explore their travel patterns.

## Features
- Extracts location data from Google Timeline JSON files.
- Generates an interactive heatmap centered on your travel data.
- Easy-to-follow instructions for setup and usage.

## Setup

### Prerequisites
- Python 3.x
- Pip (Python package manager)

### Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/HeatmapProject.git
    cd HeatmapProject
    ```

2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Place your exported `timeline.json` file in the project directory.

4. Run the script:
    ```bash
    python heatmap.py
    ```

5. Open the generated `heatmap.html` file in your browser.

## Example
Here’s an example heatmap generated from anonymized data:

![Example Heatmap](heatmap_example.html)

## How to Export Google Timeline Data
1. Open **Settings** on your Android phone and navigate to **Location**.
2. Select **Timeline** and choose your Google account.
3. Export your timeline data as a JSON file.

## Contributing
Feel free to fork this repository and submit pull requests to improve the project.

## License
This project is licensed under the MIT License.
