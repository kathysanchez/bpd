
import geopandas as gpd
import pandas as pd
from pathlib import Path
import os
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
# import matplotlib.pyplot as plt
# from matplotlib.dates import DateFormatter
# import seaborn as sns
# import folium
# from shapely.geometry import Point
# import webbrowser
import dash_bootstrap_components as dbc

print(Path.cwd())  
new_dir = Path("/home/kathy/Documents/projects/bpd") 
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

# Export weapon offenses to manually clean descriptions

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



# Make map
"""
map_center = [merged_descriptions.geometry.y.mean(), merged_descriptions.geometry.x.mean()]
m = folium.Map(location=[39.28775297151215, -76.6066912216659], zoom_start=17)

    # Add crime points 

def add_crime_marker(row):
    folium.Marker(
        location=[row.latitude, row.longitude],
    ).add_to(m)

merged_descriptions.apply(add_crime_marker, axis=1) # Apply function to each row of gdf
"""
# Save to HTML
"""
m.save("Inner_Harbor_Arrests_2024.html")
webbrowser.open("Inner_Harbor_Arrests_2024.html")
"""

# App instance
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY]) # https://dash-bootstrap-components.opensource.faculty.ai/docs/themes/explorer/

# Layout

    # Sort charges except Other

unique_charges = merged_descriptions['Charge'].dropna().unique()
sorted_charges = []
for charge in unique_charges:
    if charge != 'Other':
        sorted_charges.append(charge)
sorted_charges = sorted(sorted_charges)
if 'Other' in unique_charges:
    sorted_charges.append('Other') 
print(sorted_charges)

    # Create options 
charge_options = []

for charge in sorted_charges:
    charge_options.append({'label': charge, 'value': charge})# Label is the displayed text and value is passed to callbacks

app.layout = html.Div(
    children = [
        html.H1("Baltimore Weapons-Related Arrests, 2024"), # style={'fontFamily': 'Arial, sans-serif'},
        dbc.Row([
            dbc.Col(
                dbc.Checklist(
                    id='crime-type-filter',
                    options=charge_options,
                    value=[sorted(merged_descriptions['Charge'].dropna().unique())[0]],
                    style={'marginTop': '40px', 'marginLeft':'30px'}
                    ), 
                width=3
            ),
            dbc.Col(
                dcc.Graph(id='crime-map',
                    style={'marginTop': '40px', 'marginRight':'30px'}
                ), width=9)
        ])
    ]
)

# Callback to update the map based on crime type
@app.callback(
    Output('crime-map', 'figure'),
    Input('crime-type-filter', 'value')
)
def update_map(selected_type):
    filtered = merged_descriptions[merged_descriptions['Charge'].isin(selected_type)]

    fig = px.scatter_map(
        filtered,
        lat="latitude",
        lon="longitude",
        hover_name="Charge",
        #hover_data={"Age":True, "Sex":True, "Race":True, "Detail":True, "latitude": False, "longitude": False}, 
        custom_data=["Charge", "Age", "Sex", "Race", "Detail"],
        zoom=12,
        center={"lat": 39.2904, "lon": -76.6122},
        height=600
    )
    fig.update_traces(
        hovertemplate=", ".join([
            "<b>%{customdata[0]}</b><br>%{customdata[1]}",
            "%{customdata[2]}",
            "%{customdata[3]}<br>Detail: %{customdata[4]}"
        ])
    )

    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r":0,"t":0,"l":0,"b":0}
        #font=dict(
        #family="Open Sans, sans-serif",  
        #size=14,    
        #color="black"
        #)
    )

    return fig

# Run server
if __name__ == '__main__':
    app.run(debug=True)
