import dash
from dash import dcc, html, Input, Output, State, clientside_callback
import dash_leaflet as dl
import pandas as pd
from dash.exceptions import PreventUpdate

# Read data from Excel or CSV
try:
    df = pd.read_excel('olympics_data.xlsx', engine='openpyxl')
    print(f"Loaded {len(df)} records from olympics_data.xlsx")
except FileNotFoundError:
    try:
        df = pd.read_csv('olympics_data.csv')
        print(f"Loaded {len(df)} records from olympics_data.csv")
    except FileNotFoundError:
        print("Error: Neither olympics_data.xlsx nor olympics_data.csv found")
        # Fallback data
        df = pd.DataFrame({
            'index': range(10),
            'location': [
                'Paris, France (Summer 2024)', 'Beijing, China (Winter 2022)', 'Tokyo, Japan (Summer 2020)',
                'Pyeongchang, South Korea (Winter 2018)', 'Rio de Janeiro, Brazil (Summer 2016)',
                'Sochi, Russia (Winter 2014)', 'London, UK (Summer 2012)', 'Vancouver, Canada (Winter 2010)',
                'Beijing, China (Summer 2008)', 'Turin, Italy (Winter 2006)'
            ],
            'latitude': [48.8566, 39.9042, 35.6762, 37.3705, -22.9083, 43.5855, 51.5074, 49.2827, 39.9042, 45.0703],
            'longitude': [2.3522, 116.4074, 139.6503, 128.3903, -43.1964, 40.2020, -0.1278, -123.1207, 116.4074, 7.6869],
            'date': ['2024-07-26', '2022-02-04', '2021-07-23', '2018-02-09', '2016-08-05', '2014-02-07', '2012-07-27', '2010-02-12', '2008-08-08', '2006-02-10'],
            'country': ['France', 'China', 'Japan', 'South Korea', 'Brazil', 'Russia', 'United Kingdom', 'Canada', 'China', 'Italy'],
            'event_type': ['Summer', 'Winter', 'Summer', 'Winter', 'Summer', 'Winter', 'Summer', 'Winter', 'Summer', 'Winter'],
            'host_city': ['Paris', 'Beijing', 'Tokyo', 'Pyeongchang', 'Rio de Janeiro', 'Sochi', 'London', 'Vancouver', 'Beijing', 'Turin'],
            'attendance': [800000, 500000, 600000, 400000, 700000, 450000, 750000, 420000, 780000, 410000],
            'medal_count': [89, 65, 78, 55, 67, 62, 82, 58, 85, 54],
            'year': [2024, 2022, 2020, 2018, 2016, 2014, 2012, 2010, 2008, 2006]
        })

# Ensure required columns and index
required_columns = ['index', 'location', 'latitude', 'longitude', 'date', 'host_city', 'event_type']
for col in required_columns:
    if col not in df.columns:
        raise ValueError(f"Missing required column: {col}")
# Ensure 'index' is integer and matches range
df['index'] = df['index'].astype(int)
if not all(df['index'] == range(len(df))):
    print("Warning: 'index' column does not match expected range. Resetting index.")
    df['index'] = range(len(df))

app = dash.Dash(__name__)

# Layout
app.layout = html.Div(
    style={'display': 'flex', 'height': '100vh'},
    children=[
        html.Div(
            id='location-list',
            style={'width': '30%', 'overflowY': 'auto', 'padding': '20px'},
            children=[
                html.Div(
                    id={'type': 'location-item', 'index': i},
                    children=[
                        html.H3(f"{row['location']}", style={'margin': 0}),
                        html.P(
                            f"Date: {row['date']} | City: {row['host_city']} | Type: {row['event_type']}",
                            style={'margin': 0, 'fontSize': '14px'}
                        )
                    ],
                    style={'marginBottom': '10px', 'padding': '10px', 'cursor': 'pointer'},
                    **{'data-index': i}
                )
                for i, row in df.iterrows()
            ]
        ),
        html.Div(
            style={'width': '70%'},
            children=[
                dl.Map(
                    id='location-map',
                    center=[0, 0],
                    zoom=1,
                    children=[
                        dl.TileLayer(),  # Basic OpenStreetMap tiles
                        dl.LayerGroup(id='marker-layer', children=[
                            dl.CircleMarker(
                                center=[row['latitude'], row['longitude']],
                                radius=5,
                                color='blue',
                                fillOpacity=0.8,
                                id={'type': 'marker', 'index': i}
                            )
                            for i, row in df.iterrows()
                        ])
                    ],
                    style={'width': '100%', 'height': '100vh'}
                ),
                dcc.Store(id='selected-index', data=-1)
            ]
        )
    ]
)

@app.callback(
    Output('marker-layer', 'children'),
    Output('location-list', 'children'),
    Output('selected-index', 'data'),
    Input({'type': 'location-item', 'index': dash.ALL}, 'n_clicks'),
    Input({'type': 'marker', 'index': dash.ALL}, 'n_clicks'),
    State('location-list', 'children'),
    State({'type': 'location-item', 'index': dash.ALL}, 'id'),
    prevent_initial_call=True
)
def update_app(n_clicks_list, n_clicks_markers, current_items, item_ids):
    print("update_app CALLED")
    print(f"n_clicks_list: {n_clicks_list}")
    print(f"n_clicks_markers: {n_clicks_markers}")
    ctx = dash.callback_context
    if not ctx.triggered_id:
        print("No triggered ID")
        raise PreventUpdate

    clicked_index = -1
    if isinstance(ctx.triggered_id, dict) and ctx.triggered_id.get('type') == 'location-item':
        clicked_index = int(ctx.triggered_id['index'])
        print(f"List click: Index {clicked_index}, Location: {df.iloc[clicked_index]['location']}")
    elif isinstance(ctx.triggered_id, dict) and ctx.triggered_id.get('type') == 'marker':
        clicked_index = int(ctx.triggered_id['index'])
        print(f"Map click: Index {clicked_index}, Location: {df.iloc[clicked_index]['location']}")
    else:
        print(f"Invalid trigger: {ctx.triggered_id}")
        raise PreventUpdate

    # Update markers
    markers = [
        dl.CircleMarker(
            center=[row['latitude'], row['longitude']],
            radius=10 if i == clicked_index else 5,
            color='red' if i == clicked_index else 'blue',
            fillOpacity=0.8,
            id={'type': 'marker', 'index': i}
        )
        for i, row in df.iterrows()
    ]

    # Update list
    updated_items = [
        html.Div(
            id={'type': 'location-item', 'index': i},
            children=[
                html.H3(f"{row['location']}", style={'margin': 0}),
                html.P(
                    f"Date: {row['date']} | City: {row['host_city']} | Type: {row['event_type']}",
                    style={'margin': 0, 'fontSize': '14px'}
                )
            ],
            style={
                'marginBottom': '10px',
                'padding': '10px',
                'cursor': 'pointer',
                'border': '2px solid red' if i == clicked_index else '1px solid black'
            },
            **{'data-index': i}
        )
        for i, row in df.iterrows()
    ]

    return markers, updated_items, clicked_index

# Clientside callback for scrolling and map centering
app.clientside_callback(
    """
    function(children, selected_index) {
        console.log("Clientside triggered: selected_index=" + selected_index);
        if (selected_index >= 0) {
            const highlighted = document.querySelector(`[data-index="${selected_index}"]`);
            if (highlighted) {
                highlighted.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            const map = window.dash_leaflet_map;
            if (map && window.dash_clientside_data && window.dash_clientside_data[selected_index]) {
                const [lat, lng] = window.dash_clientside_data[selected_index];
                map.setView([lat, lng], 8);
            } else {
                console.log("Map or data not available:", { map: !!map, data: window.dash_clientside_data });
            }
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('location-list', 'id'),
    Input('location-list', 'children'),
    Input('selected-index', 'data')
)

# Inject coordinates for clientside centering
app.clientside_callback(
    """
    function() {
        console.log("Injecting coordinates");
        window.dash_clientside_data = %s;
        return window.dash_clientside.no_update;
    }
    """ % df[['latitude', 'longitude']].values.tolist(),
    Output('location-map', 'id'),
    Input('location-map', 'id')
)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)