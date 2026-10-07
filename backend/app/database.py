from pathlib import Path
import sqlite3
from contextlib import contextmanager

DB_PATH = Path(__file__).resolve().parents[1] / "crowd.db"

def connect():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c

@contextmanager
def session():
    c = connect()
    try:
        yield c
        c.commit()
    finally:
        c.close()

def risk(score):
    return "High" if score >= 80 else "Medium" if score >= 55 else "Low"

def init_db():
    with session() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS zones(
          id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,
          capacity INTEGER NOT NULL,current_count INTEGER NOT NULL DEFAULT 0,
          density_score REAL NOT NULL DEFAULT 0,risk_level TEXT NOT NULL DEFAULT 'Low',
          updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS events(
          id INTEGER PRIMARY KEY AUTOINCREMENT,zone_id INTEGER NOT NULL,
          crowd_count INTEGER NOT NULL,density_score REAL NOT NULL,
          risk_level TEXT NOT NULL,timestamp TEXT NOT NULL,
          FOREIGN KEY(zone_id) REFERENCES zones(id));
        CREATE TABLE IF NOT EXISTS alerts(
          id INTEGER PRIMARY KEY AUTOINCREMENT,zone_id INTEGER NOT NULL,
          alert_type TEXT NOT NULL,severity TEXT NOT NULL,message TEXT NOT NULL,
          created_at TEXT NOT NULL,FOREIGN KEY(zone_id) REFERENCES zones(id));
        CREATE TABLE IF NOT EXISTS system_logs(
          id INTEGER PRIMARY KEY AUTOINCREMENT,level TEXT NOT NULL,source TEXT NOT NULL,
          message TEXT NOT NULL,created_at TEXT NOT NULL);
        """)
        if c.execute("SELECT COUNT(*) n FROM zones").fetchone()["n"] == 0:
            from datetime import datetime, timezone
            import random
            zones=[("Gate A",1200),("Gate B",1200),("Exit A",1000),("Exit B",1000),
                   ("Corridor",900),("Main Stage Area",3000),("Food Court",1800),("Parking Area",2500)]
            now=datetime.now(timezone.utc).isoformat()
            for name,cap in zones:
                count=random.randint(int(cap*.12),int(cap*.35))
                d=round(count/cap*100,1)
                c.execute("INSERT INTO zones(name,capacity,current_count,density_score,risk_level,updated_at) VALUES(?,?,?,?,?,?)",
                          (name,cap,count,d,risk(d),now))

def rows(sql,args=()):
    with session() as c:
        return [dict(x) for x in c.execute(sql,args).fetchall()]

def one(sql,args=()):
    with session() as c:
        x=c.execute(sql,args).fetchone()
        return dict(x) if x else None
