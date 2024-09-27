import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import requests
import time
from collections import deque

# Initialiser l'application Dash
app = dash.Dash(__name__)

# Stocker les métriques
total_request_counts = deque(maxlen=20)
interval_request_counts = deque(maxlen=20)
error_counts = deque(maxlen=20)
timestamps = deque(maxlen=20)

# Layout du dashboard
app.layout = html.Div(children=[
    html.H1(children='Monitoring de l\'API Flask'),

    # Graphique des requêtes totales
    dcc.Graph(id='total-request-count-graph'),
    
    # Graphique des requêtes pendant chaque intervalle
    dcc.Graph(id='interval-request-count-graph'),

    # Graphique des erreurs
    dcc.Graph(id='error-count-graph'),
    
    dcc.Interval(
        id='interval-component',
        interval=2*1000,  # Mettre à jour toutes les 2 secondes
        n_intervals=0
    )
])

# Callback pour mettre à jour les graphiques
@app.callback(
    [Output('total-request-count-graph', 'figure'),
     Output('interval-request-count-graph', 'figure'),
     Output('error-count-graph', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_graph(n):
    # Récupérer les métriques de l'API Flask
    try:
        response = requests.get("http://localhost:8000/metrics")
        data = response.json()
        total_request_count = data['total_request_count']
        request_count_in_interval = data['request_count_in_interval']
        error_count = data['error_count']
    except:
        total_request_count = 0
        request_count_in_interval = 0
        error_count = 0
    
    # Stocker les métriques
    total_request_counts.append(total_request_count)
    interval_request_counts.append(request_count_in_interval)
    error_counts.append(error_count)
    timestamps.append(time.strftime('%H:%M:%S'))
    
    # Graphique pour les requêtes totales
    total_figure = {
        'data': [
            {'x': list(timestamps), 'y': list(total_request_counts), 'type': 'line', 'name': 'Total Request Count'},
        ],
        'layout': {
            'title': 'Nombre Total de Requêtes au fil du temps'
        }
    }

    # Graphique pour les requêtes pendant chaque intervalle
    interval_figure = {
        'data': [
            {'x': list(timestamps), 'y': list(interval_request_counts), 'type': 'bar', 'name': 'Requests per Interval'},
        ],
        'layout': {
            'title': 'Nombre de Requêtes par Intervalle'
        }
    }

    # Graphique pour les erreurs
    error_figure = {
        'data': [
            {'x': list(timestamps), 'y': list(error_counts), 'type': 'line', 'name': 'Error Count'},
        ],
        'layout': {
            'title': 'Nombre d\'Erreurs au fil du temps'
        }
    }
    
    return total_figure, interval_figure, error_figure

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
