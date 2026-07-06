import geopandas as gpd
import pandas as pd
from pathlib import Path
import os
import requests
import json


# Change path

print(Path.cwd())  

try: # 
    new_dir = Path(__file__).resolve().parent
except NameError:
    new_dir = Path.cwd()

print(new_dir)

os.chdir(new_dir)  
print(Path.cwd()) 

# Read CJIS codes file and clean

codes = pd.read_xml("./CJIS/cjiscode.xml") # Source: Downloaded 05/17/2025
print(codes.columns.tolist())
codes.columns = codes.columns.str.replace(" ", "_")
codes.columns = 'c_' + codes.columns.astype(str)
print(codes.columns.tolist())
codes = codes.rename(columns={
    'c_cjisclass': 'Charge'
})
codes.to_csv("./CJIS/CJIS_codes.csv", index=False)

# Define source for arrest data: Open Baltimore's live "BPD Arrests" feed
# (updated weekly, rolling from 2010-present). Replaces the frozen 2024
# GitHub-release snapshot used previously.

TARGET_YEAR = 2025

query_url = "https://egis.baltimorecity.gov/egis/rest/services/GeoSpatialized_Tables/Arrest/FeatureServer/0/query"

# Query a few days past the calendar-year boundary on each side: ArrestDateTime
# is stored as UTC epoch ms, so a strict Jan 1-Dec 31 UTC window can drop/add a
# handful of records that fall on the other side of midnight in Baltimore's
# local time. The exact year is enforced below after converting to local time.
where_clause = (
    f"ArrestDateTime >= timestamp '{TARGET_YEAR - 1}-12-25 00:00:00' "
    f"AND ArrestDateTime <= timestamp '{TARGET_YEAR + 1}-01-05 00:00:00'"
)

# Make path for geojson file

try:
    output_path = Path(__file__).parent / f"BPD_Arrests_{TARGET_YEAR}.geojson"
except NameError:
    output_path = Path.cwd() / f"BPD_Arrests_{TARGET_YEAR}.geojson"

# Read arrest geojson file, paginating since the server caps responses at
# 1,000 records per request (a full year is ~16k arrests).

if not output_path.exists():
    features = []
    page_size = 1000
    offset = 0
    while True:
        params = {
            "where": where_clause,
            "outFields": "*",
            "f": "geojson",
            "resultOffset": offset,
            "resultRecordCount": page_size,
        }
        r = requests.get(query_url, params=params)
        r.raise_for_status() # Stop app if download fails
        batch = r.json().get("features", [])
        features.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size

    with open(output_path, "w") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f)

gdf = gpd.read_file(output_path) # Use local geojson or downloaded geojson

# ArrestDateTime comes back as epoch milliseconds (UTC), not an ISO string,
# so it isn't auto-parsed to a datetime dtype by the GeoJSON reader.
gdf["ArrestDateTime"] = (
    pd.to_datetime(gdf["ArrestDateTime"], unit="ms", utc=True)
    .dt.tz_convert("America/New_York")
    .dt.tz_localize(None)
)


print(gdf.head())
gdf.columns.tolist()

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
gdf_nonmissing.ArrestDateTime.value_counts()
gdf_nonmissing.dtypes


# Subset target year only

gdf_nonmissing = gdf_nonmissing[gdf_nonmissing['ArrestDateTime'].dt.year == TARGET_YEAR]

# Check whether arrest and incidents match (they do)

gdf_nonmissing['address_test'] = gdf_nonmissing['ArrestLocation'] == gdf_nonmissing['IncidentLocation']



# Merge CJIS codes

merged = pd.merge(gdf_nonmissing, codes, on="Charge", how="left")

code_descriptions_list = merged.c_describe70.value_counts()

merged['describe_test'] = merged['c_describe100']== merged['c_describe70']

merged = merged.rename(columns={'Charge': 'Charge_CJIS'})

# Subset rows 

words = ['GUN', 'FIREARM', 'SHOOT', 'SHOT', 'ARM', 'WEAPON','HGV', 'PISTOL']
values_to_remove = ['UNARM', 'FALSE ALARM/FIRE: GIVE/CAUSE TO BE GIVEN'] 
merged_subset = merged[merged['c_describe100'].str.contains('|'.join(words), case=False, na=False)]
merged_subset = merged_subset[~merged_subset['c_describe100'].str.contains('|'.join(values_to_remove), case=False, na=False)].copy()

merged_subsetted_out = merged[~merged['c_describe100'].str.contains('|'.join(words), case=False, na=False)]

merged_offenses_list = merged_subset.c_describe100.value_counts()
merged_offenses_not_listed = merged_subsetted_out.c_describe100.value_counts()


# Change demographic values

print(merged_subset.Gender.value_counts())
print(merged_subset.Race.value_counts())

dict_sex = {"M":"Male", "F":"Female"}
dict_race = {"B":"Black", "W":"White", "U":"Race Unknown", "A":"Asian", "I":"American Indian"}

merged_subset["Gender"] = merged_subset["Gender"].replace(dict_sex)
merged_subset["Race"] = merged_subset["Race"].replace(dict_race)

# Export weapon offenses to manually clean descriptions. I manually cleaned them. This file shows how I combined and simplified Maryland crime code descriptions.

#merged_offenses_list.to_csv(".CJIS/CJIS_subset_descriptions_list.csv", index=True)


# Merge manually-cleaned descriptions 

descriptions = pd.read_csv("./CJIS/CJIS_subset_descriptions_list_edits.csv") 

merged_descriptions = pd.merge(merged_subset, descriptions, on="c_describe100", how="outer")


# Rename columns

merged_descriptions = merged_descriptions.rename(columns={
    'Gender': 'Sex',
    'c_describe100': 'Detail'
})


# Review offenses 

print(merged_descriptions.columns.tolist())

# Save 

try:
    charges_path = Path(__file__).parent / "Gun_charges_cleaned.csv"
except NameError:
    charges_path = Path.cwd() / "Gun_charges_cleaned.csv"
    
merged_descriptions.to_csv(charges_path, index=False)
