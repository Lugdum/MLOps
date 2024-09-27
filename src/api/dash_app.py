import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import requests
from collections import deque
import time

from utils import get_metrics

# Initialiser l'application Dash avec Flask
def create_dash_app(server):
    dash_app = dash.Dash(__name__, server=server, routes_pathname_prefix='/dash/')

    # Stocker les métriques pour Dash (noms différents)
    dash_total_request_counts = deque(maxlen=20)
    dash_interval_request_counts = deque(maxlen=20)
    dash_error_counts = deque(maxlen=20)
    dash_timestamps = deque(maxlen=20)

    # Layout du dashboard Dash
    dash_app.layout = html.Div(children=[
        html.H1(children='Monitoring de l\'API Flask'),

        dcc.Graph(id='total-request-count-graph'),
        dcc.Graph(id='interval-request-count-graph'),
        dcc.Graph(id='error-count-graph'),

        dcc.Interval(
            id='interval-component',
            interval=2*1000,  # Mettre à jour toutes les 2 secondes
            n_intervals=0
        )
    ])

    # Callback pour mettre à jour les graphiques dans Dash
    @dash_app.callback(
        [Output('total-request-count-graph', 'figure'),
         Output('interval-request-count-graph', 'figure'),
         Output('error-count-graph', 'figure')],
        [Input('interval-component', 'n_intervals')]
    )
    def update_graph(n):
        data = get_metrics()

        if data:
            total_request_count = data['total_request_count']
            request_count_in_interval = data['request_count_in_interval']
            error_count = data['error_count']
        else:
            total_request_count = 0
            request_count_in_interval = 0
            error_count = 0

        dash_timestamps.append(time.strftime('%H:%M:%S'))
        dash_total_request_counts.append(total_request_count)
        dash_interval_request_counts.append(request_count_in_interval)
        dash_error_counts.append(error_count)

        total_figure = {
            'data': [{'x': list(dash_timestamps), 'y': list(dash_total_request_counts), 'type': 'line', 'name': 'Total Requests'}],
            'layout': {'title': 'Nombre Total de Requêtes'}
        }

        interval_figure = {
            'data': [{'x': list(dash_timestamps), 'y': list(dash_interval_request_counts), 'type': 'bar', 'name': 'Requests per Interval'}],
            'layout': {'title': 'Requêtes par Intervalle'}
        }

        error_figure = {
            'data': [{'x': list(dash_timestamps), 'y': list(dash_error_counts), 'type': 'line', 'name': 'Error Count'}],
            'layout': {'title': 'Nombre d\'Erreurs'}
        }

        return total_figure, interval_figure, error_figure

    return dash_app
