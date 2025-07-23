
import geopandas as gpd
import pandas as pd
from pathlib import Path
import os
import plotly.express as px
from dash import Dash, callback_context, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
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
app = Dash(__name__, external_stylesheets=[dbc.themes.YETI]) # https://dash-bootstrap-components.opensource.faculty.ai/docs/themes/explorer/

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
#select_all = 'Select All'

for charge in sorted_charges:
    charge_options.append({'label': charge, 'value': charge})# Label is the displayed text and value is passed to callbacks

app.layout = html.Div(
    children = [
        html.H1("Baltimore Weapons-Related Arrests, 2024", style={'marginLeft':'30px', 'marginTop':'10px'}), 
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Select Charge", style={
                        'fontSize': '16px',
                        'color': '#333',
                        'marginBottom': '10px',
                        }),
                        html.Div(
                            dcc.Checklist(
                                id='charge-checklist-filter',
                                options=[{'label': 'Select All', 'value': 'Select All'}],
                                value=['Select All'], #sorted(merged_descriptions['Charge'].dropna().unique())[0]
                                #style={'marginRight':'30px'},
                            )
                        ),
                        html.Div(
                            dcc.Dropdown(
                                id='charge-dropdown-filter',
                                options=charge_options,
                                value=[], #sorted(merged_descriptions['Charge'].dropna().unique())[0]
                                #style={'marginRight':'30px'},
                                multi=True,
                                searchable=True
                            )
                        )
                    ],
                    width=3, #style={'marginLeft':'30px'},
                    ),
                dbc.Col(
                    dcc.Graph(id='crime-map',
                        style={'marginRight':'30px'}
                    ), 
                width=9)],
            style={'marginTop':'40px', 'marginLeft':'30px'}
        )
    ]
)

# Callback to keep dropdown and checkbox connected
@app.callback(
    [
        Output(component_id='charge-dropdown-filter', component_property='value'),
        Output(component_id='charge-checklist-filter', component_property='value')
    ],
    [
        Input(component_id='charge-checklist-filter', component_property='value'),
        Input(component_id='charge-dropdown-filter', component_property='value')
    ],
    State(component_id='charge-dropdown-filter', component_property='options')
)

def sync_checklist_dropdown(checklist_value, dropdown_value, dropdown_options):
    all_charges = []
    for option in dropdown_options:
        all_charges.append(option['value'])
    
    triggered_id = callback_context.triggered_id
    
    # If checklist triggered the callback
    if triggered_id == 'charge-checklist-filter':
        if 'Select All' in checklist_value:
            return all_charges, ['Select All']  # Select all dropdown options, keep checklist checked
        else:
            return [], []  # Clear dropdown, uncheck checklist
    
    # If dropdown triggered the callback
    if triggered_id == 'charge-dropdown-filter':
        if len(dropdown_value) == len(all_charges) and dropdown_value:
            return dropdown_value, ['Select All']  # Keep dropdown values, check checklist
        else:
            return dropdown_value, []  # Keep dropdown values, uncheck checklist
    
    # Default case for initial load or unexpected triggers
    if len(dropdown_value) == len(all_charges) and dropdown_value:
        return dropdown_value, ['Select All']
    return dropdown_value, []

# Callback to update the map based on dropdown selections
@app.callback(
    Output('crime-map', 'figure'),
    Input('charge-dropdown-filter', 'value')
)

def update_map(selected_charges):
    # If no charges selected, return empty map
    if not selected_charges:
        fig = px.scatter_mapbox(
            lat=[39.2904], lon=[-76.6122], zoom=12, height=600,
            center={"lat": 39.2904, "lon": -76.6122}, mapbox_style="carto-positron"
        )
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        return fig

    # Filter data based on selected charges
    filtered = merged_descriptions[merged_descriptions['Charge'].isin(selected_charges)]

    # Create scatter map
    fig = px.scatter_mapbox(
        filtered,
        lat="latitude",
        lon="longitude",
        hover_name="Charge",
        custom_data=["Charge", "Age", "Sex", "Race", "Detail"],
        zoom=12,
        center={"lat": 39.2904, "lon": -76.6122},
        height=600
    )
    fig.update_traces(
        hovertemplate=", ".join([
            "<b>%{customdata[0]}</b><br>Age: %{customdata[1]}",
            "Sex: %{customdata[2]}",
            "Race: %{customdata[3]}<br>Detail: %{customdata[4]}"
        ])
    )
    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )

    return fig


# Run server
if __name__ == '__main__':
    app.run(debug=True)
