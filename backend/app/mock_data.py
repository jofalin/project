import asyncio,random
from datetime import datetime,timezone
from .database import session,risk
from .logger import info,warning

running=False
speed="normal"
task=None
DELAYS={"slow":5,"normal":3,"fast":1}

def now(): return datetime.now(timezone.utc).isoformat()

async def loop():
    global running
    info("MOCK",f"Simulation started ({speed})")
    while running:
        with session() as c:
            zones=c.execute("SELECT * FROM zones").fetchall()
            for z in zones:
                delta=random.randint(-max(5,z["capacity"]//35),max(8,z["capacity"]//25))
                count=max(0,min(z["capacity"],z["current_count"]+delta))
                density=round(count/z["capacity"]*100,1)
                newrisk=risk(density); stamp=now()
                c.execute("UPDATE zones SET current_count=?,density_score=?,risk_level=?,updated_at=? WHERE id=?",
                          (count,density,newrisk,stamp,z["id"]))
                c.execute("INSERT INTO events(zone_id,crowd_count,density_score,risk_level,timestamp) VALUES(?,?,?,?,?)",
                          (z["id"],count,density,newrisk,stamp))
                if newrisk!=z["risk_level"]:
                    msg=f"{z['name']} changed from {z['risk_level']} to {newrisk} risk"
                    c.execute("INSERT INTO alerts(zone_id,alert_type,severity,message,created_at) VALUES(?,?,?,?,?)",
                              (z["id"],"Risk Level Change","CRITICAL" if newrisk=="High" else "WARNING",msg,stamp))
                    warning("MOCK",msg)
                elif newrisk=="High" and random.random()<.30:
                    msg=f"High crowd density detected in {z['name']}"
                    c.execute("INSERT INTO alerts(zone_id,alert_type,severity,message,created_at) VALUES(?,?,?,?,?)",
                              (z["id"],"Crowd Density","CRITICAL",msg,stamp))
        await asyncio.sleep(DELAYS[speed])
    info("MOCK","Simulation stopped")

async def start(value="normal"):
    global running,speed,task
    speed=value if value in DELAYS else "normal"
    if not running:
        running=True
        task=asyncio.create_task(loop())

def stop():
    global running
    running=False

def status(): return {"running":running,"speed":speed}

def reset():
    global running
    running=False
    from .database import risk
    import random
    stamp=now()
    with session() as c:
        c.execute("DELETE FROM events"); c.execute("DELETE FROM alerts"); c.execute("DELETE FROM system_logs")
        for z in c.execute("SELECT id,capacity FROM zones").fetchall():
            count=random.randint(int(z["capacity"]*.10),int(z["capacity"]*.30))
            density=round(count/z["capacity"]*100,1)
            c.execute("UPDATE zones SET current_count=?,density_score=?,risk_level=?,updated_at=? WHERE id=?",
                      (count,density,risk(density),stamp,z["id"]))
    info("MOCK","Simulation data reset")
