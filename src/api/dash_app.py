import dash
from dash import dcc, html
from dash.dependencies import Input, Output

from utils import get_metrics

# Initialiser l'application Dash avec Flask
def create_dash_app(server):
    dash_app = dash.Dash(__name__, server=server, routes_pathname_prefix='/dash/')

    dash_app.layout = html.Div(children=[
        html.H1(children="Monitoring de l'API Flask"),

        dcc.Slider(
            id='interval-count-slider',
            min=1,
            max=50,  
            step=1,
            value=10,  
            marks={i: str(i) for i in range(1, 51)},
            tooltip={"placement": "bottom", "always_visible": True},
        ),

        dcc.Graph(id='total-request-count-graph'),
        dcc.Graph(id='error-count-graph'),

        dcc.Interval(
            id='interval-component',
            interval=2*1000,  
            n_intervals=0
        )
    ])

    @dash_app.callback(
        [Output('total-request-count-graph', 'figure'),
         Output('error-count-graph', 'figure')],
        [Input('interval-component', 'n_intervals'),
         Input('interval-count-slider', 'value')]
    )
    def update_graph(n, interval_count):
        metrics = get_metrics(interval_count)

        timestamps = [row[0] for row in metrics]
        total_requests = [row[1] for row in metrics]
        errors = [row[2] for row in metrics]

        total_figure = {
            'data': [{'x': timestamps, 'y': total_requests, 'type': 'line', 'name': 'Total Requests'}],
            'layout': {'title': 'Nombre Total de Requêtes'}
        }

        error_figure = {
            'data': [{'x': timestamps, 'y': errors, 'type': 'line', 'name': 'Nombre d\'Erreurs'}],
            'layout': {'title': 'Nombre d\'Erreurs'}
        }

        return total_figure, error_figure

    return dash_app