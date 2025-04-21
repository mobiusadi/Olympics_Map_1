import dash
from dash import dcc, html, Input, Output, State, callback_context, clientside_callback
import plotly.express as px
import pandas as pd
from dash.exceptions import PreventUpdate

# Dataset: Last 10 Olympic Games
data = {
    'index': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    'location': [
        'Paris, France (Summer 2024)', 'Beijing, China (Winter 2022)', 'Tokyo, Japan (Summer 2020)',
        'Pyeongchang, South Korea (Winter 2018)', 'Rio de Janeiro, Brazil (Summer 2016)',
        'Sochi, Russia (Winter 2014)', 'London, UK (Summer 2012)', 'Vancouver, Canada (Winter 2010)',
        'Beijing, China (Summer 2008)', 'Turin, Italy (Winter 2006)'
    ],
    'latitude': [48.8566, 39.9042, 35.6762, 37.3705, -22.9083, 43.5855, 51.5074, 49.2827, 39.9042, 45.0703],
    'longitude': [2.3522, 116.4074, 139.6503, 128.3903, -43.1964, 40.2020, -0.1278, -123.1207, 116.4074, 7.6869],
    'date': ['2024-07-26', '2022-02-04', '2021-07-23', '2018-02-09', '2016-08-05', '2014-02-07', '2012-07-27', '2010-02-12', '2008-08-08', '2006-02-10']
}
df = pd.DataFrame(data)
print(f"Number of locations: {len(df)}")  # Expected: 10

app = dash.Dash(__name__)

# Initial map figure
fig = px.scatter_mapbox(
    df,
    lat="latitude",
    lon="longitude",
    hover_name="location",
    hover_data={"date": True, "latitude": ":.4f", "longitude": ":.4f", "index": True},
    custom_data=["index"],  # Pass index for clickData
    zoom=1,
    height=800
).update_traces(
    marker=dict(size=10, opacity=0.8),
    hovertemplate="<b>%{hovertext}</b><br>Date: %{customdata[1]}<br>Lat: %{customdata[2]:.4f}<br>Lon: %{customdata[3]:.4f}<extra></extra>",
    selector=dict(mode='markers')
).update_layout(
    mapbox_style="open-street-map",
    margin={"r": 0, "t": 0, "l": 0, "b": 0}
)

app.layout = html.Div(
    style={'display': 'flex', 'height': '100vh'},
    children=[
        html.Div(
            id='location-list',
            style={'width': '30%', 'overflowY': 'auto', 'padding': '20px'},
            children=[
                html.Div(
                    id={'type': 'location-item', 'index': i},
                    children=[html.H3(f"{row['location']} - {row['date']}", style={'margin': 0})],
                    style={'marginBottom': '10px', 'border': '1px solid #ddd', 'padding': '10px', 'cursor': 'pointer'}
                )
                for i, row in df.iterrows()
            ]
        ),
        html.Div(
            style={'width': '70%'},
            children=[
                dcc.Graph(id='location-map', figure=fig),
                dcc.Store(id='selected-index', data=-1)
            ]
        ),
    ]
)

@app.callback(
    Output('location-map', 'figure'),
    Output('location-list', 'children'),
    Output('selected-index', 'data'),
    Input({'type': 'location-item', 'index': dash.ALL}, 'n_clicks'),
    Input('location-map', 'clickData'),
    State('location-map', 'figure'),
    State('location-list', 'children'),
    State({'type': 'location-item', 'index': dash.ALL}, 'id'),
    prevent_initial_call=True
)
def update_app(n_clicks, click_data, current_figure, current_items, item_ids):
    print("update_app CALLED")
    ctx = callback_context
    if not ctx.triggered_id:
        raise PreventUpdate

    clicked_index = -1
    if isinstance(ctx.triggered_id, dict) and ctx.triggered_id.get('type') == 'location-item':
        clicked_index = int(ctx.triggered_id['index'])
        print(f"List click: Index {clicked_index}, Location: {df.iloc[clicked_index]['location']}")
    elif click_data and 'points' in click_data and 'customdata' in click_data['points'][0]:
        clicked_index = int(click_data['points'][0]['customdata'][0])
        print(f"Map click: Index {clicked_index}, Location: {df.iloc[clicked_index]['location']}")
    else:
        print("Invalid trigger or clickData")
        raise PreventUpdate

    clicked_row = df.iloc[clicked_index]

    # Update map
    updated_figure = dict(current_figure)
    updated_figure['layout']['mapbox'].update({
        'center': {'lat': clicked_row['latitude'], 'lon': clicked_row['longitude']},
        'zoom': 8
    })
    updated_figure['data'][0]['marker']['color'] = ['blue'] * len(df)
    updated_figure['data'][0]['marker']['color'][clicked_index] = 'red'
    updated_figure['data'][0]['marker']['size'] = [10] * len(df)
    updated_figure['data'][0]['marker']['size'][clicked_index] = 15

    # Update list
    updated_items = []
    for i, item in enumerate(current_items):
        new_item = dict(item)
        default_style = {'marginBottom': '10px', 'border': '1px solid #ddd', 'padding': '10px', 'cursor': 'pointer'}
        new_item['props']['style'] = default_style
        if i == clicked_index:
            new_item['props']['style'] = {'marginBottom': '10px', 'border': '2px solid red', 'padding': '10px', 'cursor': 'pointer'}
        updated_items.append(new_item)

    return updated_figure, updated_items, clicked_index

# Clientside callback for scrolling
app.clientside_callback(
    """
    function(children, selected_index) {
        console.log("Clientside scrolling triggered: selected_index=" + selected_index);
        if (selected_index >= 0) {
            const highlighted = document.querySelector('[style*="border: 2px solid red"]');
            if (highlighted) {
                highlighted.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('location-list', 'id'),
    Input('location-list', 'children'),
    Input('selected-index', 'data'),
    prevent_initial_call=True
)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)