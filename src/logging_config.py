import logging

def configure_logging():
    # Logger pour les requêtes utilisateur
    user_logger = logging.getLogger('user_logger')
    user_logger.setLevel(logging.INFO)
    user_handler = logging.FileHandler('/app/logs/app.log')
    user_formatter = logging.Formatter('%(asctime)s - %(message)s')
    user_handler.setFormatter(user_formatter)
    user_logger.addHandler(user_handler)

    # Logger pour les requêtes de métriques
    metrics_logger = logging.getLogger('metrics_logger')
    metrics_logger.setLevel(logging.INFO)
    metrics_handler = logging.FileHandler('/app/logs/metrics.log')
    metrics_formatter = logging.Formatter('%(asctime)s - %(message)s')
    metrics_handler.setFormatter(metrics_formatter)
    metrics_logger.addHandler(metrics_handler)

    return user_logger, metrics_logger
