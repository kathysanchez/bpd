
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from shapely.geometry import Point
from pathlib import Path
import os
import webbrowser

print(Path.cwd())  
new_dir = Path("/home/kathy/Documents/projects/bpd") 
os.chdir(new_dir)  
print(Path.cwd()) 

gdf = gpd.read_file("BPD_Arrests.geojson") # Source: Open Baltimore. Date updated 3/10/2025 Date created 3/10/2021
print(gdf.head())

# Check current CRS
print(gdf.crs) # Check coordinate reference sys
if gdf.crs != "EPSG:4326":
    print("Reproject to WGS 84")
    gdf = gdf.to_crs("EPSG:4326")  # Reproject to WGS 84

# Add latitude and longitude columns
gdf["longitude"] = gdf.geometry.x
gdf["latitude"] = gdf.geometry.y

# Drop missing
gdf_nonmissing = gdf.dropna(subset=['latitude', 'longitude'])
print(gdf_nonmissing.head())

gdf_nonmissing.columns.tolist()
gdf_nonmissing.ArrestDateTime.value

# TODO subset df




map_center = [gdf.geometry.y.mean(), gdf.geometry.x.mean()]
m = folium.Map(location=map_center, zoom_start=12)

# Add crime points to the map using apply()
def add_crime_marker(row):
    folium.Marker(
        location=[row.latitude, row.longitude],
    ).add_to(m)

# Apply the function to each row of the GeoDataFrame
gdf.apply(add_crime_marker, axis=1)
# Save to an HTML file
m.save("map_arrests.html")
webbrowser.open("map_arrests.html")




