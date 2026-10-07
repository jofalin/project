import logging
from pathlib import Path
from datetime import datetime, timezone
from .database import session

LOG_DIR=Path(__file__).resolve().parents[1]/"logs"
LOG_DIR.mkdir(parents=True,exist_ok=True)
file_logger=logging.getLogger("crowd")
file_logger.setLevel(logging.INFO)
if not file_logger.handlers:
    h=logging.FileHandler(LOG_DIR/"app.log",encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    file_logger.addHandler(h)

def log(level,source,message):
    now=datetime.now(timezone.utc).isoformat()
    getattr(file_logger,level.lower(),file_logger.info)(f"{source} | {message}")
    try:
        with session() as c:
            c.execute("INSERT INTO system_logs(level,source,message,created_at) VALUES(?,?,?,?)",
                      (level,source,message,now))
    except Exception as exc:
        file_logger.error(f"LOGGER_DB_ERROR | {exc}")

def info(source,message): log("INFO",source,message)
def warning(source,message): log("WARNING",source,message)
def error(source,message): log("ERROR",source,message)
