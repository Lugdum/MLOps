import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import requests
import time
from collections import deque

# Initialiser l'application Dash
app = dash.Dash(__name__)

# Stocker les métriques
request_counts = deque(maxlen=20)
timestamps = deque(maxlen=20)

# Layout du dashboard
app.layout = html.Div(children=[
    html.H1(children='Monitoring de l\'API Flask'),
    
    dcc.Graph(id='request-count-graph'),
    
    dcc.Interval(
        id='interval-component',
        interval=2*1000,  # Mettre à jour toutes les 2 secondes
        n_intervals=0
    )
])

# Callback pour mettre à jour le graphique
@app.callback(
    Output('request-count-graph', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_graph(n):
    # Récupérer les métriques de l'API Flask
    try:
        response = requests.get("http://localhost:8000/metrics")
        data = response.json()
        request_count = data['request_count']
    except:
        request_count = 0
    
    # Stocker les métriques
    request_counts.append(request_count)
    timestamps.append(time.strftime('%H:%M:%S'))
    
    # Créer le graphique
    figure = {
        'data': [
            {'x': list(timestamps), 'y': list(request_counts), 'type': 'line', 'name': 'Request Count'},
        ],
        'layout': {
            'title': 'Nombre de Requêtes au fil du temps'
        }
    }
    
    return figure

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
