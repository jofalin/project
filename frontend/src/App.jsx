import React,{useEffect,useState} from "react";
import {Activity,Map,FileText,ScrollText,Radio,ShieldAlert,Database,RefreshCw,Play,Square,RotateCcw} from "lucide-react";
import {api} from "./api";
import Intelligence from "./Intelligence";

const nav=[["dashboard","Dashboard",Activity],["intelligence","Predictive Intelligence",Activity],["map","SVG Risk Map",Map],["reports","Reports",FileText],["logs","System Logs",ScrollText],["mock","Mock Data Tool",Radio]];
const Badge=({level})=><span className={"badge "+String(level).toLowerCase()}>{level}</span>;
const Stat=({label,value,Icon})=><div className="stat"><Icon/><div><small>{label}</small><strong>{value}</strong></div></div>;

function Layout({page,setPage,children}){
 const [s,setS]=useState({running:false,speed:"normal"});
 useEffect(()=>{const load=()=>api.status().then(setS).catch(()=>{});load();const t=setInterval(load,2000);return()=>clearInterval(t)},[]);
 return <div className="shell"><aside><div className="brand"><ShieldAlert/><div><b>CROWD OPS</b><small>COMMAND CENTER</small></div></div><div className="sys"><i className={s.running?"live":""}/>{s.running?"SIMULATION LIVE":"SYSTEM READY"}</div><nav>{nav.map(([id,label,Icon])=><button className={page===id?"active":""} onClick={()=>setPage(id)} key={id}><Icon/>{label}</button>)}</nav><footer><Database/> SQLite / FastAPI</footer></aside><main><header><div><small>AI CROWD INTELLIGENCE</small><h1>{nav.find(x=>x[0]===page)[1]}</h1></div><span>{new Date().toLocaleTimeString()} <button onClick={()=>location.reload()}><RefreshCw size={15}/></button></span></header>{children}</main></div>
}

function Dashboard(){
 const [d,setD]=useState(null);
 useEffect(()=>{const f=()=>api.summary().then(setD).catch(()=>{});f();const t=setInterval(f,4000);return()=>clearInterval(t)},[]);
 if(!d)return <div className="loading">Connecting to FastAPI…</div>;
 return <section><div className="stats"><Stat label="Total Crowd Count" value={d.total_crowd_count.toLocaleString()} Icon={Activity}/><Stat label="Active Zones" value={d.active_zones} Icon={Map}/><Stat label="High Risk Zones" value={d.risk_counts.High} Icon={ShieldAlert}/><Stat label="Medium Risk Zones" value={d.risk_counts.Medium} Icon={ShieldAlert}/><Stat label="Low Risk Zones" value={d.risk_counts.Low} Icon={ShieldAlert}/><Stat label="Active Alerts" value={d.active_alerts} Icon={Radio}/></div>
 <div className="cols"><div className="panel"><h2>Crowd Density Trend</h2><p>Recent event crowd counts</p><svg className="chart" viewBox="0 0 700 220" preserveAspectRatio="none">{d.recent_events.length>1&&<polyline fill="none" stroke="#38bdf8" strokeWidth="3" points={d.recent_events.slice().reverse().map((e,i)=>i/(d.recent_events.length-1)*700+","+((220-e.crowd_count/Math.max(...d.recent_events.map(x=>x.crowd_count),1))*190)).join(" ")}/>}</svg></div>
 <div className="panel"><h2>Risk Distribution</h2><p>Current zone risk levels</p><div className="donut" style={{"--a":(d.risk_counts.High/d.active_zones*100)+"%","--b":((d.risk_counts.High+d.risk_counts.Medium)/d.active_zones*100)+"%"}}><b>{d.active_zones}</b></div><div className="legend"><span>● High {d.risk_counts.High}</span><span>● Medium {d.risk_counts.Medium}</span><span>● Low {d.risk_counts.Low}</span></div></div></div>
 <div className="cols"><div className="panel"><h2>Alert Timeline</h2><p>Recent alerts by severity</p><div className="alert-timeline">{d.recent_alerts.slice().reverse().map((a,i)=><div key={a.id||i} className="alert-bar"><span>{new Date(a.created_at).toLocaleTimeString()}</span><i className={a.severity==="CRITICAL"?"critical":"warning"} style={{height:(a.severity==="CRITICAL"?80:45)+"%"}}/></div>)}</div></div><div className="panel"><h2>Recent Alerts</h2><Table rows={d.recent_alerts} headers={["Time","Zone","Severity","Message"]} render={a=><><td>{new Date(a.created_at).toLocaleTimeString()}</td><td>{a.zone_name}</td><td><Badge level={a.severity}/></td><td>{a.message}</td></>}/></div>
 <div className="panel"><h2>Recent Zone Activity</h2><Table rows={d.zones} headers={["Zone","Crowd","Density","Risk"]} render={z=><><td>{z.name}</td><td>{z.current_count.toLocaleString()}</td><td>{z.density_score}%</td><td><Badge level={z.risk_level}/></td></>}/></div></div></section>
}

function Table({rows,headers,render}){return <div className="table"><table><thead><tr>{headers.map(h=><th key={h}>{h}</th>)}</tr></thead><tbody>{rows.map((x,i)=><tr key={x.id||i}>{render(x)}</tr>)}</tbody></table>{!rows.length&&<div className="empty">No data available.</div>}</div>}

function RiskMap(){
 const [zs,setZs]=useState([]),[selected,setSelected]=useState(null),[zoom,setZoom]=useState(1),[pan,setPan]=useState({x:0,y:0}),[drag,setDrag]=useState(null);
 useEffect(()=>{const f=()=>api.zones().then(setZs).catch(()=>{});f();const t=setInterval(f,3000);return()=>clearInterval(t)},[]);
 const boxes=[{x:25,y:35,w:175,h:75},{x:220,y:35,w:175,h:75},{x:415,y:35,w:175,h:75},{x:610,y:35,w:175,h:75},{x:120,y:145,w:300,h:100},{x:450,y:145,w:330,h:125},{x:120,y:275,w:300,h:115},{x:450,y:295,w:330,h:95}];
 const c=z=>z.risk_level==="High"?"#ef4444":z.risk_level==="Medium"?"#f59e0b":"#22c55e";
 return <section><div className="toolbar"><div><b>WHOLE VENUE / LIVE RISK</b><p>Click zones for details. Drag to pan and use controls to zoom.</p></div><div><button onClick={()=>setZoom(Math.min(2.5,zoom+.15))}>+</button><button onClick={()=>setZoom(Math.max(.55,zoom-.15))}>−</button><button onClick={()=>{setZoom(1);setPan({x:0,y:0})}}>Reset</button></div></div><div className="map-grid"><div className="svgbox"><svg viewBox="0 0 820 430" onMouseDown={e=>setDrag({x:e.clientX-pan.x,y:e.clientY-pan.y})} onMouseMove={e=>drag&&setPan({x:e.clientX-drag.x,y:e.clientY-drag.y})} onMouseUp={()=>setDrag(null)} onMouseLeave={()=>setDrag(null)}><g transform={"translate("+pan.x+" "+pan.y+") scale("+zoom+")"}>{zs.map((z,i)=>{const b=boxes[i];return <g key={z.id} onClick={()=>setSelected(z)}><title>{z.name} — {z.current_count} people — {z.density_score}% density — {z.risk_level} risk</title><rect x={b.x} y={b.y} width={b.w} height={b.h} rx="10" fill={c(z)} fillOpacity=".18" stroke={c(z)} strokeWidth="3"/><text x={b.x+b.w/2} y={b.y+b.h/2-3}>{z.name}</text><text className="sub" x={b.x+b.w/2} y={b.y+b.h/2+17}>{z.current_count} / {z.capacity}</text></g>})}</g></svg><div className="legend"><span>● Low</span><span>● Medium</span><span>● High</span></div></div>{selected?<div className="panel detail"><h2>{selected.name}</h2><Badge level={selected.risk_level}/><strong>{selected.current_count.toLocaleString()}</strong><p>Current crowd count</p><div className="bar"><i style={{width:Math.min(selected.density_score,100)+"%"}}/></div><div className="row">Capacity <b>{selected.capacity.toLocaleString()}</b></div><div className="row">Density <b>{selected.density_score}%</b></div><div className="row">Updated <b>{new Date(selected.updated_at).toLocaleTimeString()}</b></div></div>:<div className="panel detail empty">Select a zone.</div>}</div></section>
}

function Reports(){
 const [period,setPeriod]=useState("daily"),[d,setD]=useState(null),[startDate,setStartDate]=useState(""),[endDate,setEndDate]=useState("");
 useEffect(()=>{api.report(period,startDate,endDate).then(setD).catch(()=>{})},[period,startDate,endDate]);
 const csv=()=>window.open("http://localhost:8000/reports/"+period+"/csv?"+new URLSearchParams({...(startDate?{start_date:startDate}:{}),...(endDate?{end_date:endDate}:{})}),"_blank");
 return <section><div className="toolbar"><div className="tabs">{["daily","weekly","monthly"].map(p=><button className={period===p?"active":""} onClick={()=>setPeriod(p)} key={p}>{p}</button>)}</div><div><input type="date" value={startDate} onChange={e=>setStartDate(e.target.value)}/><input type="date" value={endDate} onChange={e=>setEndDate(e.target.value)}/><button onClick={csv}>Export CSV</button><button onClick={()=>print()}>Print</button></div></div>{d&&<div className="report"><small>COMMAND REPORT</small><h2>{d.period} Crowd Intelligence Report</h2><div className="metrics">{Object.entries(d.metrics).map(([k,v])=><div key={k}><small>{k.replaceAll("_"," ")}</small><strong>{v}{k.includes("density")||k.includes("utilization")?"%":""}</strong></div>)}</div><div className="panel"><h2>Zone Utilization</h2>{d.zone_utilization.map(z=><div className="util" key={z.name}><span>{z.name}</span><div><i style={{width:Math.min(z.utilization,100)+"%"}}/></div><b>{z.utilization}%</b></div>)}</div></div>}</section>
}

function Logs(){
 const [level,setLevel]=useState("ALL"),[search,setSearch]=useState(""),[logs,setLogs]=useState([]);
 useEffect(()=>{const f=()=>api.logs(level,search).then(setLogs).catch(()=>{});f();const t=setInterval(f,4000);return()=>clearInterval(t)},[level,search]);
 return <section><div className="toolbar"><select value={level} onChange={e=>setLevel(e.target.value)}><option>ALL</option><option>INFO</option><option>WARNING</option><option>ERROR</option></select><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search logs…"/></div><div className="panel"><Table rows={logs} headers={["Timestamp","Level","Source","Message"]} render={l=><><td>{new Date(l.created_at).toLocaleString()}</td><td><Badge level={l.level==="ERROR"?"High":l.level==="WARNING"?"Medium":"Low"}/></td><td>{l.source}</td><td className="mono">{l.message}</td></>}/></div></section>
}

function Mock(){
 const [s,setS]=useState({running:false,speed:"normal"}),[speed,setSpeed]=useState("normal");
 useEffect(()=>{const f=()=>api.status().then(setS).catch(()=>{});f();const t=setInterval(f,1500);return()=>clearInterval(t)},[]);
 return <section><div className="hero"><div><small>SIMULATION CONTROL</small><h2>Generate venue activity</h2><p>Crowd counts, density, risk changes, alerts, events and logs.</p></div><div className={s.running?"orb live":"orb"}>{s.running?"LIVE":"IDLE"}</div></div><div className="cols"><div className="panel"><h2>Simulation Speed</h2><div className="speed">{["slow","normal","fast"].map(x=><button className={speed===x?"active":""} onClick={()=>setSpeed(x)} key={x}>{x}</button>)}</div><div className="actions"><button disabled={s.running} onClick={()=>api.start(speed)}><Play/> Start Simulation</button><button disabled={!s.running} onClick={()=>api.stop()}><Square/> Stop Simulation</button><button onClick={()=>api.reset()}><RotateCcw/> Reset Data</button></div></div><div className="panel"><h2>Generated Signals</h2><ul><li>Live crowd count changes</li><li>Density and risk transitions</li><li>Automatic high-risk alerts</li><li>Historical event records</li><li>INFO / WARNING / ERROR logs</li><li>SQLite persistence</li></ul></div></div></section>
}

export default function App(){
 const [page,setPage]=useState("dashboard");
 return <Layout page={page} setPage={setPage}>{page==="dashboard"?<Dashboard/>:page==="intelligence"?<Intelligence/>:page==="map"?<RiskMap/>:page==="reports"?<Reports/>:page==="logs"?<Logs/>:<Mock/>}</Layout>
}