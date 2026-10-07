import React,{useEffect,useState} from "react";
import {Activity,CloudRain,ArrowRight,TriangleAlert,MessageSquare,Play,RefreshCw,Check,X} from "lucide-react";
import {api} from "./api";
import "./intelligence.css";

function Panel({title,children,wide=false}){return <div className={"intel-panel"+(wide?" wide":"")}><div className="intel-panel-title">{title}</div>{children}</div>}

export default function Intelligence(){
 const [data,setData]=useState(null),[sop,setSop]=useState(null),[advisories,setAdvisories]=useState([]),[sim,setSim]=useState(null);
 const [message,setMessage]=useState(""),[chat,setChat]=useState([]),[density,setDensity]=useState(95),[trend,setTrend]=useState(18),[weatherMod,setWeatherMod]=useState(.2),[busy,setBusy]=useState(false);

 const load=async()=>{try{const [summary,weather,schedule,flow,incidents,reports,history,sopData,ads]=await Promise.all([
  api.summary(),api.weather(),api.schedule(),api.predictiveFlow(),api.incidents(),api.intelligenceReports(),api.riskHistory(),api.sop(),api.advisories()
 ]);setData({summary,weather,schedule,flow:flow.predictions,incidents:incidents.incidents,reports:reports.reports,history:history.history});setSop(sopData);setAdvisories(ads.advisories)}catch(e){}};
 useEffect(()=>{load();const t=setInterval(load,5000);return()=>clearInterval(t)},[]);

 const runSim=async()=>{setBusy(true);try{setSim(await api.simulation({label:"Gate A stress test",weather_modifier:Number(weatherMod),zones:{"Gate A":{density:Number(density),trend:Number(trend),direction:"Zone B"}}}))}finally{setBusy(false)}};
 const send=async()=>{if(!message.trim())return;const m=message.trim();setMessage("");setChat(x=>[...x,{who:"you",text:m}]);const r=await api.operatorChat(m,chat);setChat(x=>[...x,{who:"ai",text:r.answer,source:r.source}])};
 const decision=async(id,approve)=>{const r=approve?await api.approve(id):await api.reject(id);setAdvisories(x=>x.map(a=>a.id===id?{...a,status:r.status}:a))};

 if(!data)return <div className="loading">Connecting to predictive intelligence…</div>;
 const top=data.summary.zones.slice().sort((a,b)=>b.density_score-a.density_score)[0];
 return <section className="intel">
  <div className="intel-hero">
   <div><div className="intel-kicker">PREDICTIVE CROWD INTELLIGENCE</div><h2>Sense → understand → predict → recommend</h2><p>Integrated with the SQLite command center, reports, simulation and operator controls.</p></div>
   <button onClick={load} className="intel-refresh"><RefreshCw size={15}/> Refresh</button>
  </div>
  <div className="intel-stats">
   <div><small>TOP RISK</small><strong>{top?.name||"—"}</strong><span>{top?.density_score||0}% density</span></div>
   <div><small>PROPAGATION</small><strong>{Math.round((data.flow[0]?.probability||0)*100)}%</strong><span>{data.flow[0]?.source_zone} → {data.flow[0]?.target_zone}</span></div>
   <div><small>WEATHER</small><strong>{data.weather.condition}</strong><span>{data.weather.temperature_c}°C · +{data.weather.risk_modifier.toFixed(2)} modifier</span></div>
   <div><small>ACTIVE ALERTS</small><strong>{data.summary.active_alerts}</strong><span>database-backed</span></div>
  </div>

  <div className="intel-grid">
   <Panel title="Predictive Crowd Flow">
    <div className="flow-list">{data.flow.map(p=><div className="flow-row" key={p.id}><div><b>{p.source_zone}</b><ArrowRight size={15}/><b>{p.target_zone}</b><small>{p.reason}</small></div><strong>{Math.round(p.probability*100)}%<em>{p.eta_seconds}s</em></strong></div>)}</div>
   </Panel>
   <Panel title="Context">
    <div className="context-row"><CloudRain size={18}/><div><b>{data.weather.condition}</b><span>{data.weather.rain_mm} mm rain · {data.weather.visibility_km} km visibility · {data.weather.wind_kph} kph wind</span></div></div>
    <div className="context-row"><Activity size={18}/><div><b>{data.schedule.current_event?.event||data.schedule.next_event?.event||"No scheduled event"}</b><span>{data.schedule.current_event?"Active now":data.schedule.next_event?"in "+data.schedule.next_event.minutes_until+" min":"No active event"}</span></div></div>
    <div className="incident-mini">{data.incidents.map((i,n)=><div key={n}><TriangleAlert size={14}/><span>{i.title} — {i.message}</span></div>)}</div>
   </Panel>

   <Panel title="Venue Risk History">
    <div className="history-chart">{data.history.map((h,i)=><div className="history-col" key={h.time}><i style={{height:(h.gate_a||0)+"%"}}/><span>{h.time}</span></div>)}</div>
    <small className="caption">Gate A density progression</small>
   </Panel>
   <Panel title="Multi-Modal Reports">
    <div>{data.reports.map(r=><div className="report-row" key={r.id}><span className={"report-tag "+r.type.toLowerCase()}>{r.type}</span><div><b>{r.id}</b><p>{r.message}</p></div><small>{r.age_seconds}s</small></div>)}</div>
   </Panel>

   <Panel title="Dynamic SOP" wide>
    {sop&&<><div className="sop-grid"><div><small>OBSERVATION</small><p>{sop.observation}</p></div><div><small>TREND</small><p>{sop.trend}</p></div><div><small>PREDICTION</small><p>{sop.prediction}</p></div></div><div className="sop-actions">{sop.recommendations.map((r,i)=><div key={i}>0{i+1} · {r}</div>)}</div><div className="human-note">Human review required — AI drafts only. Operator approval comes before field action.</div></>}
   </Panel>

   <Panel title="What-If Simulation">
    <div className="sim-form"><label>Gate A density<input type="number" min="0" max="100" value={density} onChange={e=>setDensity(e.target.value)}/></label><label>Trend<input type="number" value={trend} onChange={e=>setTrend(e.target.value)}/></label><label>Weather modifier<input type="number" min="0" max="1" step=".01" value={weatherMod} onChange={e=>setWeatherMod(e.target.value)}/></label></div>
    <button onClick={runSim} disabled={busy} className="intel-primary"><Play size={14}/> {busy?"Running…":"Run simulation"}</button>
    {sim&&<div className="sim-result"><b>{sim.summary}</b><span>Highest pressure: {sim.highest_risk_zone}</span>{sim.predictions.slice(0,2).map(p=><div key={p.id}>{p.source_zone} → {p.target_zone}: {Math.round(p.probability*100)}% / {p.eta_seconds}s</div>)}</div>}
   </Panel>

   <Panel title="Operator AI">
    <div className="chat-box">{chat.length?chat.map((m,i)=><div key={i} className={m.who==="you"?"chat-you":"chat-ai"}>{m.text}</div>):<div className="chat-empty">Ask about risk, movement, weather, schedule or recommendations.</div>}</div>
    <div className="chat-form"><input value={message} onChange={e=>setMessage(e.target.value)} onKeyDown={e=>e.key==="Enter"&&send()} placeholder="Ask operator AI…"/><button onClick={send}><MessageSquare size={15}/></button></div>
   </Panel>

   <Panel title="Advisories Awaiting Review" wide>
    {advisories.length?advisories.map(a=><div className="advisory" key={a.id}><div><span className="advisory-cat">{a.category}</span><b>{a.prediction}</b><p>{a.recommendation}</p></div><div className="advisory-actions">{a.status==="DRAFT"?<><button onClick={()=>decision(a.id,true)}><Check size={14}/> Approve</button><button onClick={()=>decision(a.id,false)}><X size={14}/> Reject</button></>:<span>{a.status}</span>}</div></div>):<div className="chat-empty">No generated advisories.</div>}
   </Panel>
  </div>
 </section>
}