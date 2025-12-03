# -*- coding: utf-8 -*-
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(app):
    log_level_str = app.config.get('LOG_LEVEL', 'INFO')
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    if not app.testing:
        logs_dir = os.path.join(os.path.dirname(app.root_path), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        file_handler = RotatingFileHandler(os.path.join(logs_dir, 'backend.log'), maxBytes=10*1024*1024, backupCount=10)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)
    app.logger.info(f'Logger initialized - Level: {log_level_str}')
