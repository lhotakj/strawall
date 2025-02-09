from enum import Enum


class StatsType(Enum):
    yord = {"name": "Yearly Ride Distance (km)", "scale": 1000, "decimal": 2, "unit": "km"}
    yore = {"name": "Yearly Ride Elevation (m)", "scale": 1,    "decimal": 0, "unit": "m"}
    word = {"name": "Weekly Ride Distance (km)", "scale": 1000, "decimal": 2, "unit": "km"}
    wore = {"name": "Weekly Ride Elevation (m)", "scale": 1,    "decimal": 0, "unit": "m"}
