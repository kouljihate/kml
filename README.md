# Farm Irrigation Editor

A modular Streamlit application for agricultural irrigation design.

## Workflow

1. Upload and inspect KML.
2. Define land, well, basin, and sectors.
3. Add irrigation zones.
4. Generate rows and trees.
5. Create 90 mm, 63 mm, 32 mm, and 16 mm pipe networks.
6. Add valves, fittings, air valves, and flush points.
7. Run hydraulic checks.
8. Export KML, DXF, GeoJSON, CSV, and EPANET files.

## Start

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
