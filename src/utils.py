import sqlite3
import time

# Simuler une base de données d'utilisateurs avec des rôles
users = {
    "admin": {"password": "adminpass", "role": "admin"},
    "user": {"password": "userpass", "role": "user"},
    "normal": {"password": "normalpass", "role": "normal"}
}

# Définir les rôles et leur accès
roles_permissions = {
    "admin": ["predict", "logs", "metrics"],
    "user": ["predict"],
    "normal": []
}

DATABASE = 'metrics.db'

# Création d'une table pour stocker les métriques
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_requests INTEGER,
            errors INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()

# Insertion d'une nouvelle métrique
def update_metrics(total=0, error=0):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO metrics (total_requests, errors)
        VALUES (?, ?)
    ''', (total, error))
    
    conn.commit()
    conn.close()

# Récupérer les X dernières métriques, en ajoutant des 0 si nécessaire
def get_metrics(last_n):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Sélectionner les dernières X entrées, groupées par intervalle de 2 secondes
    cursor.execute('''
        SELECT strftime('%H:%M:%S', timestamp), SUM(total_requests), SUM(errors)
        FROM metrics
        GROUP BY (strftime('%s', timestamp) / 2)  -- Grouper par intervalles de 2 secondes
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (last_n,))
    
    rows = cursor.fetchall()
    conn.close()

    # Générer les intervalles manquants avec des 0
    timestamps = [time.strftime('%H:%M:%S', time.localtime(time.time() - 2 * i)) for i in range(last_n)]
    metrics_dict = {row[0]: (row[1], row[2]) for row in rows}

    result = []
    for ts in timestamps:
        if ts in metrics_dict:
            result.append((ts, metrics_dict[ts][0], metrics_dict[ts][1]))
        else:
            result.append((ts, 0, 0))  # Ajouter des 0 si aucune donnée n'existe pour cet intervalle

    return result