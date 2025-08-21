from pathlib import Path
import os


print(Path.cwd())  
new_dir = Path(__file__).parent
os.chdir(new_dir)  
print(Path.cwd()) 

import bpd_cleaning
from dash import Dash, callback_context, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px



# App instance
app = Dash(__name__, external_stylesheets=[dbc.themes.YETI]) # https://dash-bootstrap-components.opensource.faculty.ai/docs/themes/explorer/

# Import mostly cleaned data

merged_descriptions = bpd_cleaning.merged_descriptions

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

charge_options = [] # Create options 

for charge in sorted_charges:
    charge_options.append({'label': charge, 'value': charge})# Label is the displayed text and value is passed to callbacks

    # Create bar data
merged_descriptions_counts = merged_descriptions.groupby('Charge').count()
print(merged_descriptions.dtypes)
merged_descriptions_counts['Arrests'] = merged_descriptions_counts['ChargeDescription']
print(merged_descriptions_counts.head())
merged_descriptions_counts = merged_descriptions_counts.reset_index()

# Layout

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
                            )
                        ),
                        html.Div(
                            dcc.Dropdown(
                                id='charge-dropdown-filter',
                                options=charge_options,
                                value=sorted_charges, #sorted(merged_descriptions['Charge'].dropna().unique())[0]
                                multi=True,
                                searchable=True
                            )
                        )
                    ],
                    width=3, #style={'height': '350px'}
                    ),
                dbc.Col(
                    dcc.Graph(id='crime-map',
                        style={'marginRight':'30px', 'height': '350px'}
                    ), 
                width=9)],
            style={'marginTop':'40px', 'marginLeft':'30px', 'height': '390px'}
        ),
    dbc.Row(
        [    
            dbc.Col(width=3), 
            dbc.Col(
                html.Div(
                    dcc.Graph(
                        id='crime-bar',
                        style={'marginRight':'30px'}
                    )
                )
            )
        ],
        style={'marginLeft':'30px', 'height': '350px'}
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

def sync_checklist_dropdown(checklist_value, dropdown_value, dropdown_options): #these arguments are my component properties, 'value'
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
    # Make empty map for no selections
    if not selected_charges:
        fig = px.scatter_mapbox(
            lat=[39.2904], lon=[-76.6122], zoom=12, height=350,
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
        height=350
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

# Callback to update the bar fig based on dropdown selections
@app.callback(
    Output('crime-bar', 'figure'),
    Input('charge-dropdown-filter', 'value')
)
def update_bar(selected_charges):
    if not selected_charges:
        bar = px.bar(
        )
        return bar

    # Filter data based on selected charges
    filtered = merged_descriptions_counts[merged_descriptions_counts['Charge'].isin(selected_charges)]
    
    # Create bar
    bar = px.bar(
        filtered,
        x='Charge',
        y='Arrests'
    )
    
    bar.update_layout(
        xaxis_title=None,
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
        paper_bgcolor='rgba(0,0,0,0)' 
    )

    return bar

# Flask for Gunicorn
server = app.server

# Run locally 
app.run_server(
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 8050)),
    debug=False
)


# # Run server for local testing
# if __name__ == '__main__':
#     app.run(debug=False)
