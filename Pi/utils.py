import os
import yaml
import logging
from logging.handlers import RotatingFileHandler
import shutil
from datetime import datetime

# Logging Levels:
# DEBUG, INFO, WARNING, ERROR, CRITICAL       



def get_config():
        with open("./config.yaml", "r") as f:
                return(yaml.safe_load(f))

conf = get_config()
log_dir = conf["logging"]["dir"]

def create_logger(name, level = "INFO"):
        os.makedirs(log_dir, exist_ok=True)
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        log_path = os.path.join(log_dir, f"{name}.log")
        handler = RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=3)
        formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
        return logger

def ensure_free_space(path, min_free_gb, max_days):
    total, used, free = shutil.disk_usage(path)
    free_gb = free / (1024**3)
    if free_gb >= min_free_gb:
        return

    files = []
    for root, _, filenames in os.walk(path):
        for fn in filenames:
            full = os.path.join(root, fn)
            files.append((full, os.path.getmtime(full)))

    files.sort(key=lambda x: x[1])  # oldest first
    for full, _ in files:
        try:
            os.remove(full)
        except Exception:
            pass
        total, used, free = shutil.disk_usage(path)
        free_gb = free / (1024**3)
        if free_gb >= min_free_gb:
            break

def timestamped_filename(prefix, ext):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}.{ext}"

