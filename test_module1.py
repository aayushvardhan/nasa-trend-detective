import matplotlib.pyplot as plt
from src.catalog import REGIONS, VARIABLES
from src.data_loader import fetch_region

region = "Indo-Gangetic Plain"
var = "T2M"

series, points = fetch_region(var, REGIONS[region]["bbox"], 2000, 2023)

print(f"{VARIABLES[var]['name']} in {region}")
print("Shape of point table :", points.shape)   # expect (288, 9)
print("Missing values       :", int(series.isna().sum()))
print(series.head(12).round(2))

series.plot(title=f"{VARIABLES[var]['name']} - {region}", ylabel=VARIABLES[var]["units"])
plt.show()