
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import seaborn as sns
import folium
from shapely.geometry import Point
from pathlib import Path
import os
import webbrowser
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

print(Path.cwd())  
new_dir = Path("/home/kathy/Documents/projects/bpd") 
os.chdir(new_dir)  
print(Path.cwd()) 

# Read CJIS codes file and clean

codes = pd.read_xml("cjiscode.xml") # Source: Downloaded 05/17/2025
print(codes.columns.tolist())
codes.columns = codes.columns.str.replace(" ", "_")
codes.columns = 'c_' + codes.columns.astype(str)
print(codes.columns.tolist())
codes = codes.rename(columns={
    'c_cjisclass': 'Charge'
})
codes.to_csv("CJIS_codes.csv", index=False)

# Read arrest geojson file

gdf = gpd.read_file("BPD_Arrests.geojson") # Source: Open Baltimore. Date updated 3/10/2025 Date created 3/10/2021
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


# Subset 2024 only

gdf_nonmissing = gdf_nonmissing[gdf_nonmissing['ArrestDateTime'].dt.year == 2024]


# Merge CJIS codes

merged = pd.merge(gdf_nonmissing, codes, on="Charge", how="left")

code_descriptions_list = merged.c_describe70.value_counts()

merged['describe_test'] = merged['c_describe100']== merged['c_describe70']


# Subset rows 

words = ['GUN', 'FIREARM', 'SHOOT', 'SHOT', 'ARM', 'WEAPON','HGV', 'PISTOL']
values_to_remove = ['UNARM'] 
merged_subset = merged[merged['c_describe100'].str.contains('|'.join(words), case=False, na=False)]
merged_subset = merged_subset[~merged_subset['c_describe100'].str.contains('|'.join(values_to_remove), case=False, na=False)].copy()

merged_subsetted_out = merged[~merged['c_describe100'].str.contains('|'.join(words), case=False, na=False)]


merged_offenses_list = merged_subset.c_describe100.value_counts()
merged_offenses_not_listed = merged_subsetted_out.c_describe100.value_counts()


# Check whether arrest and incidents match (they do)

merged_subset['address_test'] = merged_subset['ArrestLocation'] ==merged_subset['IncidentLocation']


# Rename columns

merged_subset = merged_subset.rename(columns={
    'Gender': 'Sex'
})








# Subset certain offenses

offenses_list = pd.DataFrame(gdf_nonmissing.ChargeDescription.value_counts())



# Make map

map_center = [gdf_nonmissing.geometry.y.mean(), gdf_nonmissing.geometry.x.mean()]
m = folium.Map(location=[39.28775297151215, -76.6066912216659], zoom_start=17)

    # Add crime points 

def add_crime_marker(row):
    folium.Marker(
        location=[row.latitude, row.longitude],
    ).add_to(m)

subset_df.apply(add_crime_marker, axis=1) # Apply function to each row of gdf

# Save to HTML
"""
m.save("Inner_Harbor_Arrests_2024.html")
webbrowser.open("Inner_Harbor_Arrests_2024.html")
"""



# TODO add different color markers and legend for offense types

print(subset_df.ChargeDescription.value_counts())


rename_dict = {
    "ARMED CAR JACKING": "Armed Carjacking/Attempted", 
    "ARMED CARJACKING": "Armed Carjacking/Attempted", 
    "ATT ARMED CARJACKING": "Armed Carjacking/Attempted", 
    "FIREARM VIOLATION": "Armed Carjacking/Attempted", 

    "ARMED ROBBERY": "Armed Robbery/Attempted", 
    "COMMERCIAL ARMED ROBBERY": "Armed Robbery/Attempted", 
    "ARMED COMMERCIAL ROBBERY": "Armed Robbery/Attempted", 
    "ATTEMPT ARMED ROBBERY": "Armed Robbery/Attempted", 
    "ATTEMPTED ARMED ROBBERY": "Armed Robbery/Attempted", 
    "ATT. ARMED ROBBERY": "Armed Robbery/Attempted", 
    "DANGEROUS WEAPON": "Armed Robbery/Attempted", # Assault
    "AGGRAVATED ASSAULT BY SHOOTING": "Armed Robbery/Attempted", 
    
    "HANDGUN VOILATION": "Firearm Violation", 
    "HANGUN VIOLATION": "Firearm Violation", 
    "HANDGUN VIOLATION": "Firearm Violation", 
    "HAND GUN VIOLATION": "Firearm Violation", 
    "WEAPON VIOLATION": "Firearm Violation", 
    "AMMO/FIREARM": "Firearm Violation", 
    "DISCHARGING FIREARM": "Firearm Violation", 
    "HANDGUN": "Firearm Violation", 
    "HANDGUN VIOLATION/CDS": "Firearm Violation", 
    "HANDGUN VILOATION": "Firearm Violation", 
    "HANDGUN ON PERSON": "Firearm Violation", 
    "CDS-POSS OF FIREARMS": "Firearm Violation", 
    "WEAPONS VIOLATION": "Firearm Violation", 
    "FIREARM POSSESSION WITH FELONY": "Firearm Violation", 
    "CONCEALED DANGEROUS WEAPON": "Firearm Violation", 
    "DISCHARGING OF FIREARM": "Firearm Violation", 
    
    "POSSESSION OF BB GUN": "Air Pistol/BB Gun Violation", 
    "BB GUN": "Air Pistol/BB Gun Violation", 
    "BB GUN VIOLATION": "Air Pistol/BB Gun Violation", 
    "POSS OF BB GUN": "Air Pistol/BB Gun Violation", 
    "AIR PISTOL/BB GUN": "Air Pistol/BB Gun Violation"
}

# Replace values
subset_df["Description"] = subset_df["ChargeDescription"] 

subset_df["Description"] = subset_df["Description"].replace(rename_dict)

# Review handgun violation charges

handgun_violations = subset_df[subset_df['ChargeDescription'] == 'HANDGUN VIOLATION']





handgun_vios_dict = {
    "1 0493": "Possess/Wear/Use/Carry/Transport in a Drug Offense", # puwc drug
    
    "1 0692": "Possess/Wear/Carry with Conviction", # puwc conviction cds
    "1 1106": "Possess with Conviction", # possession after convicted of a disqualifying crime
    "1 1609": "Possess with Conviction", # possess  after convicted
    "1 1610": "Possess with Conviction", # possession rifle shotgun after conviction violent crime
    
    "1 1686": "Firearm Violation", # Firearm no serial number
    "2 5210": "Firearm Violation", # sell rent transfer without license
            
    "1 1783": "Unlawful Wear/Carry", # unlawful wear carry 
    "1 1784": "Unlawful Wear/Carry", # unlawful wear carry 
    "1 1785": "Unlawful Wear/Carry", # unlawful wear carry 
    "1 1786": "Unlawful Wear/Carry", # unlawful wear carry 
    
    "1 2801": "Possess, Sell, Transfer Stolen Firearm", # stolen firearm - possess, sell transfer
    
    "1 5285": "Possess Firearm Under 21", # Possess firearm under age 21
    
    "2 5299": "Possess/Use Machine Gun", # Possess/use machine gun
    "1 1314": "Possess/Use Machine Gun", # Possess/use machine gun 
    
    "2 0480": "Other", # Motor vehicle theft
    "1 0881": "Other", # drugs 
    "1 1119": "Other", # drugs
    "1 1692": "Other", # puwc drug
    "1 1769": "Other" # impersonating leo    
}    

# Replace values
subset_df["Charge_HandgunVios"] = subset_df["Charge"] 

subset_df["Charge_HandgunVios"] = subset_df["Charge_HandgunVios"].replace(handgun_vios_dict)


# TODO drop these
    "1 1415" # Assault - presume 
    "1 1420" # Assault

print(subset_df.Description.value_counts())

# App instance
app = Dash(__name__)

# Layout
app.layout = html.Div([
    html.H1("Baltimore Firearm-Related Arrests, 2024"),
    dcc.Dropdown(
        id='crime-type-filter',
        options=[
            {'label': ct, 'value': ct} for ct in sorted(subset_df['ChargeDescription'].dropna().unique())
        ],
        value=sorted(subset_df['ChargeDescription'].dropna().unique())[0],
        clearable=False
    ),
    dcc.Graph(id='crime-map')
])

# Callback to update the map based on crime type
@app.callback(
    Output('crime-map', 'figure'),
    Input('crime-type-filter', 'value')
)
def update_map(selected_type):
    filtered = subset_df[subset_df['ChargeDescription'] == selected_type]

    fig = px.scatter_map(
        filtered,
        lat="latitude",
        lon="longitude",
        hover_name="ChargeDescription",
        hover_data=["Age", "Gender", "Race"], 
        zoom=12,
        height=600
    )

    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r":0,"t":40,"l":0,"b":0},
        font=dict(
        family="Open Sans, sans-serif",  
        size=14,    
        color="black"
    )
    )

    return fig

# Run server
if __name__ == '__main__':
    app.run(debug=True)
