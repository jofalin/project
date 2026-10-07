from datetime import datetime,timedelta,timezone
import csv,io
from fastapi import FastAPI,HTTPException,Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from .database import init_db,rows,one
from .logger import info,error
from .mock_data import start,stop,status,reset

app=FastAPI(title="AI Crowd Intelligence API",version="1.0")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:5173","http://127.0.0.1:5173"],
                   allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

class StartBody(BaseModel):
    speed:str="normal"

@app.on_event("startup")
def startup():
    init_db(); info("SYSTEM","API started")

@app.get("/health")
def health(): return {"status":"ok"}

@app.get("/zones")
def zones(): return rows("SELECT * FROM zones ORDER BY id")

@app.get("/zones/{zone_id}")
def zone(zone_id:int):
    x=one("SELECT * FROM zones WHERE id=?",(zone_id,))
    if not x: raise HTTPException(404,"Zone not found")
    return x

@app.get("/events")
def events(limit:int=Query(100,ge=1,le=1000)):
    return rows("SELECT e.*,z.name zone_name FROM events e JOIN zones z ON z.id=e.zone_id ORDER BY e.timestamp DESC LIMIT ?",(limit,))

@app.get("/alerts")
def alerts(limit:int=Query(100,ge=1,le=500)):
    return rows("SELECT a.*,z.name zone_name FROM alerts a JOIN zones z ON z.id=a.zone_id ORDER BY a.created_at DESC LIMIT ?",(limit,))

@app.get("/logs")
def logs(level:str|None=None,search:str|None=None,limit:int=Query(200,ge=1,le=1000)):
    sql="SELECT * FROM system_logs WHERE 1=1"; args=[]
    if level and level!="ALL": sql+=" AND level=?"; args.append(level.upper())
    if search: sql+=" AND (message LIKE ? OR source LIKE ?)"; args += [f"%{search}%",f"%{search}%"]
    sql+=" ORDER BY created_at DESC LIMIT ?"; args.append(limit)
    return rows(sql,args)

@app.get("/dashboard/summary")
def summary():
    zs=zones()
    al=rows("SELECT a.*,z.name zone_name FROM alerts a JOIN zones z ON z.id=a.zone_id ORDER BY a.created_at DESC LIMIT 8")
    ev=rows("SELECT e.*,z.name zone_name FROM events e JOIN zones z ON z.id=e.zone_id ORDER BY e.timestamp DESC LIMIT 40")
    counts={"High":0,"Medium":0,"Low":0}
    for z in zs: counts[z["risk_level"]]+=1
    cutoff=(datetime.now(timezone.utc)-timedelta(minutes=10)).isoformat()
    active=one("SELECT COUNT(*) n FROM alerts WHERE created_at>=?",(cutoff,))["n"]
    return {"total_crowd_count":sum(z["current_count"] for z in zs),"active_zones":len(zs),
            "risk_counts":counts,"active_alerts":active,"zones":zs,"recent_alerts":al,"recent_events":ev}

def period_range(period, start_date=None, end_date=None):
    if start_date:
        start=datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
    else:
        days={"Daily":1,"Weekly":7,"Monthly":30}[period]
        start=datetime.now(timezone.utc)-timedelta(days=days)
    if end_date:
        end=datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)+timedelta(days=1)
    else:
        end=datetime.now(timezone.utc)+timedelta(seconds=1)
    return start.isoformat(),end.isoformat()

def report(period,start_date=None,end_date=None):
    start,end=period_range(period,start_date,end_date)
    stat=one("SELECT COALESCE(AVG(density_score),0) avg,COALESCE(MAX(crowd_count),0) peak FROM events WHERE timestamp>=? AND timestamp<?",(start,end))
    alerts_n=one("SELECT COUNT(*) n FROM alerts WHERE created_at>=? AND created_at<?",(start,end))["n"]
    high=one("SELECT COUNT(*) n FROM events WHERE risk_level='High' AND timestamp>=? AND timestamp<?",(start,end))["n"]
    util=rows("SELECT z.name,ROUND(COALESCE(AVG(e.crowd_count),0)*100.0/z.capacity,1) utilization FROM zones z LEFT JOIN events e ON e.zone_id=z.id AND e.timestamp>=? AND e.timestamp<? GROUP BY z.id",(start,end))
    return {"period":period,"start":start,"end":end,
            "metrics":{"average_crowd_density":round(stat["avg"],1),"peak_crowd_count":stat["peak"],
                       "alert_count":alerts_n,"high_risk_events":high,
                       "zone_utilization":round(sum(x["utilization"] for x in util)/len(util),1) if util else 0},
            "zone_utilization":util}

@app.get("/reports/{period}")
def get_report(period:str,start_date:str|None=None,end_date:str|None=None):
    if period.lower() not in ("daily","weekly","monthly"): raise HTTPException(404,"Unknown report")
    return report(period.title(),start_date,end_date)

@app.get("/reports/{period}/csv")
def report_csv(period:str,start_date:str|None=None,end_date:str|None=None):
    data=get_report(period,start_date,end_date)
    out=io.StringIO(); w=csv.writer(out)
    w.writerow(["Report",data["period"]])
    for k,v in data["metrics"].items(): w.writerow([k.replace("_"," ").title(),v])
    w.writerow([]); w.writerow(["Zone","Utilization %"])
    for z in data["zone_utilization"]: w.writerow([z["name"],z["utilization"]])
    return StreamingResponse(iter([out.getvalue()]),media_type="text/csv",
      headers={"Content-Disposition":f"attachment; filename={period}-report.csv"})

@app.get("/mock/status")
def mock_status(): return status()

@app.post("/mock/start")
async def mock_start(body:StartBody):
    await start(body.speed); info("MOCK",f"Start requested: {body.speed}"); return status()

@app.post("/mock/stop")
def mock_stop():
    stop(); info("MOCK","Stop requested"); return status()

@app.post("/mock/reset")
def mock_reset():
    reset(); return status()

@app.exception_handler(Exception)
async def handle_error(request,exc):
    error("API",f"{request.method} {request.url.path}: {exc}")
    return JSONResponse(status_code=500,content={"detail":"Internal server error"})
