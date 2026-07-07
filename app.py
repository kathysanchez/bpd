from pathlib import Path
import os

print(Path.cwd())
try:
    new_dir = Path(__file__).resolve().parent # Run script
except NameError:
    new_dir = Path.cwd()

os.chdir(new_dir)
print(Path.cwd())

#import bpd_cleaning
from dash import Dash, callback_context, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd

# App instance
app = Dash(__name__, external_stylesheets=[dbc.themes.YETI]) # https://dash-bootstrap-components.opensource.faculty.ai/docs/themes/explorer/

# Import mostly cleaned data

#merged_descriptions = bpd_cleaning.merged_descriptions
try: # Assign path
    gun_charges_path = Path(__file__).parent / "Gun_charges_cleaned.csv"
except NameError:
    gun_charges_path = Path.cwd() / "Gun_charges_cleaned.csv"


merged_descriptions = pd.read_csv(gun_charges_path) # Read csv

# Rows with a missing Sex/District/Neighborhood would otherwise never match any
# filter selection (NaN isin([...]) is always False) and silently vanish from
# every view, even with "Select All" checked. Give them an explicit bucket.
for _col in ("Sex", "District", "Neighborhood"):
    merged_descriptions[_col] = merged_descriptions[_col].fillna("Unknown")

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
    charge_options.append({'label': charge, 'value': charge}) # Label is the displayed text and value is passed to callbacks

# Sex / District / Neighborhood filters, same shape as the charge filter

def options_for(column):
    values = sorted(merged_descriptions[column].dropna().unique().tolist())
    return values, [{'label': v, 'value': v} for v in values]

sex_values, sex_options = options_for('Sex')
district_values, district_options = options_for('District')
neighborhood_values, neighborhood_options = options_for('Neighborhood')

# Charge color palette for the map and bar chart. There are 15 charges but
# only 8 hues that stay clearly distinct from each other (see the dataviz
# skill's palette), so the 8 most common charges each get their own color and
# everything rarer folds into one neutral "Other charges" bucket — the exact
# charge is still shown on hover, only the dot color is shared for the tail.
CHARGE_PALETTE = ['#2a78d6', '#1baf7a', '#eda100', '#008300', '#4a3aa7', '#e34948', '#e87ba4', '#eb6834']
OTHER_CHARGE_COLOR = '#898781'
OTHER_CHARGE_LABEL = 'Other charges (see hover)'

top_charges = merged_descriptions['Charge'].value_counts().head(len(CHARGE_PALETTE)).index.tolist()
charge_color_map = dict(zip(top_charges, CHARGE_PALETTE))
charge_color_map[OTHER_CHARGE_LABEL] = OTHER_CHARGE_COLOR
charge_color_order = top_charges + [OTHER_CHARGE_LABEL]

merged_descriptions['Charge_Color_Group'] = merged_descriptions['Charge'].where(
    merged_descriptions['Charge'].isin(top_charges), OTHER_CHARGE_LABEL
)

# Links for dashboard footer, each shown as an icon (muted gray, #636efa on
# hover). "website" uses the favicon in assets/icons; the rest are inline SVGs.
links = [
    ("Website", "https://kathysanchez.github.io/", "website"),
    ("GitHub", "https://github.com/kathysanchez", "github"),
    ("LinkedIn", "https://linkedin.com/in/kathy-sanchez-", "linkedin"),
    ("X", "https://x.com/gkathysanchez", "x"),
]

    # Build link components
link_components = []
for label, url, icon in links:
    link_components.append(
        html.A(
            html.Span(className=f'footer-icon footer-icon-{icon}'),
            href=url,
            target="_blank",
            rel="noopener noreferrer",
            className="footer-icon-link",
            title=label,
            **{'aria-label': label}
        )
    )

# Build one "Select All" checklist + searchable multi-dropdown filter block.
# Charge, Sex, District, and Neighborhood all use this same shape.
def make_filter(label, filter_id, options, values):
    checklist_id = f'{filter_id}-checklist-filter'
    dropdown_id = f'{filter_id}-dropdown-filter'
    return html.Div(
        [
            html.Label(label, className='filter-label'),
            html.Div(
                dcc.Checklist(
                    id=checklist_id,
                    options=[{'label': 'Select All', 'value': 'Select All'}],
                    value=['Select All'],
                )
            ),
            html.Div(
                dcc.Dropdown(
                    id=dropdown_id,
                    options=options,
                    value=values,
                    multi=True,
                    searchable=True,
                    maxHeight=500
                )
            )
        ],
        className='filter-block'
    )

FILTERS = [
    ('charge', 'Select Charge', charge_options, sorted_charges),
    ('sex', 'Select Sex', sex_options, sex_values),
    ('district', 'Select District', district_options, district_values),
    ('neighborhood', 'Select Neighborhood', neighborhood_options, neighborhood_values),
]

# One card wrapper shared by the map and the bar chart, so both read as the
# same kind of dashboard "widget" as the filter panel.
def chart_card(title, graph_id, extra_class):
    return html.Div(
        [
            html.H5(title, className='chart-title'),
            dcc.Graph(id=graph_id)
        ],
        className=f'chart-card {extra_class}'
    )

# Dashboard layout

app.layout = dbc.Container(
    fluid=True,
    className='page-container',
    children=[
        html.Div(
            [
                html.H1("Baltimore Weapon-Related 911 Arrests, 2025", className='heading'),
                html.P(
                    "Weapon-related arrests arising from 911 calls that occurred across Baltimore City in 2025",
                    className='subheading'
                ),
            ],
            className='header-block'
        ),

        # First row - Filter column and figures column
        dbc.Row(
            [
                dbc.Col(
                    [
                        make_filter(label, filter_id, options, values)
                        for filter_id, label, options, values in FILTERS
                    ],
                    xs=12, sm=12, md=3,
                    className='filter-col card-panel'
                    ),
                dbc.Col(
                    [
                        chart_card("Arrest Locations", 'crime-map', 'map-container'),
                        chart_card("Arrests by Charge", 'crime-bar', 'bar-container'),
                    ],
                    xs=12, sm=12, md=9,
                ),
            ],
            className='first-row g-4',
        ),

    # Second row - "Data"

    dbc.Row(
        dbc.Col(
                [
                    html.H4("Data"),
                    html.P([
                        "The arrests represent the leading charge for each arrest that resulted from a 911 call in 2025. Unless specified, weapon-related arrests may include weapons other than guns. The data source is Baltimore City's publicly available Baltimore City dataset: 911 Calls For Service 2025. The crimes shown here do not match Maryland’s official crime codes one-to-one. I combined and simplified some of the official crime codes to make the data easier to interpret. For full details on the cleaning and analysis, see the ",
                        html.A(
                            "GitHub repo",
                            href="https://github.com/kathysanchez/bpd",
                            target="_blank",
                            style={'color': '#636efa', 'textDecoration': 'none'}
                        ),
                        "."
                    ],
                    className="paragraph-text"
                    )
                ],
                xs=12, sm=12, md=6,
            ),
            className='content-row'
        ),

    # Third row - "About"
    dbc.Row(
        dbc.Col(
            [
                html.H4("About"),
                html.P(
                    "This is an ongoing personal project by Kathy Sanchez, a researcher living in Baltimore County. I’m making this dashboard to better understand violent and non-violent gun-related crimes in the city.",
                    className="paragraph-text"
                    )
            ],
            xs=12, sm=12, md=6,
        ),
        className='content-row'
        ),

    # Fourth row - Footer

    dbc.Row(
        dbc.Col(
            html.P(link_components, className="profile-links"),
            xs=12, sm=12, md=12,
        ),
        className='footer-row'
        )
    ]
)

# Callback to keep a dropdown and its "Select All" checklist connected. One of
# these gets registered per filter (charge, sex, district, neighborhood).
def register_sync_callback(filter_id):
    checklist_id = f'{filter_id}-checklist-filter'
    dropdown_id = f'{filter_id}-dropdown-filter'

    @app.callback(
        [
            Output(component_id=dropdown_id, component_property='value'),
            Output(component_id=checklist_id, component_property='value')
        ],
        [
            Input(component_id=checklist_id, component_property='value'),
            Input(component_id=dropdown_id, component_property='value')
        ],
        State(component_id=dropdown_id, component_property='options')
    )
    def sync_checklist_dropdown(checklist_value, dropdown_value, dropdown_options):
        all_values = [option['value'] for option in dropdown_options]

        triggered_id = callback_context.triggered_id

        # If checklist triggered the callback
        if triggered_id == checklist_id:
            if 'Select All' in checklist_value:
                return all_values, ['Select All']  # Select all dropdown options, keep checklist checked
            else:
                return [], []  # Clear dropdown, uncheck checklist

        # If dropdown triggered the callback
        if triggered_id == dropdown_id:
            if dropdown_value and len(dropdown_value) == len(all_values):
                return dropdown_value, ['Select All']  # Keep dropdown values, check checklist
            else:
                return dropdown_value, []  # Keep dropdown values, uncheck checklist

        # Default case for initial load or unexpected triggers
        if dropdown_value and len(dropdown_value) == len(all_values):
            return dropdown_value, ['Select All']
        return dropdown_value, []

    return sync_checklist_dropdown

for _filter_id, *_ in FILTERS:
    register_sync_callback(_filter_id)

FILTER_INPUTS = [Input(f'{filter_id}-dropdown-filter', 'value') for filter_id, *_ in FILTERS]


def filter_data(selected_charges, selected_sexes, selected_districts, selected_neighborhoods):
    # Deselecting everything in any one filter means "show nothing", same as
    # the original charge-only behavior.
    if not (selected_charges and selected_sexes and selected_districts and selected_neighborhoods):
        return merged_descriptions.iloc[0:0]
    return merged_descriptions[
        merged_descriptions['Charge'].isin(selected_charges)
        & merged_descriptions['Sex'].isin(selected_sexes)
        & merged_descriptions['District'].isin(selected_districts)
        & merged_descriptions['Neighborhood'].isin(selected_neighborhoods)
    ]


EMPTY_MAP_CENTER = {"lat": 39.2904, "lon": -76.6122}

# Callback to update the map based on filter selections
@app.callback(
    Output('crime-map', 'figure'),
    FILTER_INPUTS
)
def update_map(selected_charges, selected_sexes, selected_districts, selected_neighborhoods):
    filtered = filter_data(selected_charges, selected_sexes, selected_districts, selected_neighborhoods)

    # Make empty map for no selections
    if filtered.empty:
        fig = px.scatter_mapbox(
            lat=[39.2904], lon=[-76.6122], zoom=12, height=480,
            center=EMPTY_MAP_CENTER, mapbox_style="carto-positron"
        )
        fig.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            font=dict(color="#333")
        )
        return fig

    # Create scatter map, colored by charge (the 8 most common charges each
    # get their own color; everything rarer shares one neutral color and
    # keeps its specific charge name on hover)
    fig = px.scatter_mapbox(
        filtered,
        lat="latitude",
        lon="longitude",
        color="Charge_Color_Group",
        color_discrete_map=charge_color_map,
        category_orders={"Charge_Color_Group": charge_color_order},
        hover_name="Charge",
        custom_data=["Charge", "Age", "Sex", "Race", "Detail"],
        zoom=12,
        center=EMPTY_MAP_CENTER,
        height=480
    )
    fig.update_traces(
        marker=dict(size=8, opacity=0.85),
        hovertemplate=", ".join([
            "<b>%{customdata[0]}</b><br>Age: %{customdata[1]}",
            "Sex: %{customdata[2]}",
            "Race: %{customdata[3]}<br>Detail: %{customdata[4]}"
        ])
    )
    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        font=dict(color="#333"),
        legend=dict(
            title=dict(text="Charge", font=dict(size=11)),
            font=dict(size=10),
            bgcolor="rgba(255,255,255,0.85)",
            itemsizing="constant",
            yanchor="top", y=0.99,
            xanchor="left", x=0.01
        )
    )

    return fig

# Callback to update the bar chart based on filter selections
@app.callback(
    Output('crime-bar', 'figure'),
    FILTER_INPUTS
)
def update_bar(selected_charges, selected_sexes, selected_districts, selected_neighborhoods):
    filtered = filter_data(selected_charges, selected_sexes, selected_districts, selected_neighborhoods)

    if filtered.empty:
        bar = px.bar(
        )
        return bar

    # Recount from the filtered rows so the bar reflects all active filters,
    # not just the charge selection
    counts = (
        filtered
        .groupby(['Charge', 'Charge_Color_Group'])
        .size()
        .reset_index(name='Arrests')
    )

    # Create bar, using the same charge colors as the map. The legend is
    # already shown on the map, so it's turned off here to avoid duplication.
    bar = px.bar(
        counts,
        x='Charge',
        y='Arrests',
        color='Charge_Color_Group',
        color_discrete_map=charge_color_map,
        category_orders={'Charge_Color_Group': charge_color_order, 'Charge': sorted_charges},
        height=420
    )

    # Drop plotly's auto-generated "Charge_Color_Group=..." hover line (an
    # artifact of the internal color-grouping column, not meant to be shown)
    bar.update_traces(
        hovertemplate="Charge=%{x}<br>Arrests=%{y}<extra></extra>"
    )

    bar.update_layout(
        xaxis_title=None,
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#333"),
        showlegend=False,
        margin={"l": 10, "r": 10, "t": 10, "b": 10}
    )

    return bar

# Flask for Gunicorn
server = app.server

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8050)),
        debug=True
    )

