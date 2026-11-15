"""Catalog of variables and regions available in the tool."""

VARIABLES = {
    "T2M": {
        "name": "Air Temperature at 2 m",
        "units": "°C",
        "source": "MERRA-2 (via NASA POWER)",
        "definition": (
            "Average air temperature measured 2 metres above the surface, "
            "the standard height for weather stations."
        ),
    },
    "PRECTOTCORR": {
        "name": "Precipitation (bias-corrected)",
        "units": "mm/day",
        "source": "MERRA-2 corrected with GPM IMERG (via NASA POWER)",
        "definition": (
            "Average daily rain and snow falling on the surface, "
            "adjusted against satellite and gauge observations."
        ),
    },
    "GWETROOT": {
        "name": "Root Zone Soil Wetness",
        "units": "fraction (0-1)",
        "source": "MERRA-2 (via NASA POWER)",
        "definition": (
            "How full of water the soil is in the zone plant roots reach. "
            "0 = completely dry, 1 = fully saturated."
        ),
    },
}

# Bounding boxes: (lat_min, lat_max, lon_min, lon_max)
REGIONS = {
    "Indo-Gangetic Plain": {
        "bbox": (24.0, 30.0, 75.0, 88.0),
        "note": "Densely populated, heavily irrigated, monsoon-driven.",
    },
    "Sahel (West Africa)": {
        "bbox": (12.0, 16.0, -10.0, 10.0),
        "note": "Semi-arid belt south of the Sahara; famous multi-decade rainfall swings.",
    },
    "Amazon Basin": {
        "bbox": (-10.0, 0.0, -70.0, -55.0),
        "note": "Largest rainforest; sensitive to drought and deforestation.",
    },
    "Central Australia": {
        "bbox": (-28.0, -22.0, 128.0, 140.0),
        "note": "Arid interior with high temperature variability.",
    },
}