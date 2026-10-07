let running=false;
let advisoryState=[
  {id:"demo-1",category:"CROWD_FLOW",status:"DRAFT",prediction:"Zone B has 81% predicted congestion probability in about 52 seconds.",recommendation:"Position trained volunteers near Zone B and guide visitors toward an alternate route if available."},
  {id:"demo-2",category:"WEATHER",status:"DRAFT",prediction:"Movement may slow under light rain conditions.",recommendation:"Increase monitoring around high-density transition areas."}
];
const zones=[
  {id:1,name:"Gate A",capacity:1200,current_count:984,density_score:82,risk_level:"High",updated_at:new Date().toISOString()},
  {id:2,name:"Gate B",capacity:1200,current_count:684,density_score:57,risk_level:"Medium",updated_at:new Date().toISOString()},
  {id:3,name:"Exit A",capacity:1000,current_count:612,density_score:61,risk_level:"Medium",updated_at:new Date().toISOString()},
  {id:4,name:"Exit B",capacity:1000,current_count:315,density_score:31.5,risk_level:"Low",updated_at:new Date().toISOString()},
  {id:5,name:"Corridor",capacity:900,current_count:666,density_score:74,risk_level:"Medium",updated_at:new Date().toISOString()},
  {id:6,name:"Main Stage Area",capacity:3000,current_count:2460,density_score:82,risk_level:"High",updated_at:new Date().toISOString()},
  {id:7,name:"Food Court",capacity:1800,current_count:846,density_score:47,risk_level:"Low",updated_at:new Date().toISOString()},
  {id:8,name:"Parking Area",capacity:2500,current_count:520,density_score:20.8,risk_level:"Low",updated_at:new Date().toISOString()}
];
const flows=[
  {id:"a",source_zone:"Gate A",target_zone:"Zone B",probability:.81,eta_seconds:52,severity:"HIGH",reason:"82% density, trend +12%, movement toward Zone B."},
  {id:"b",source_zone:"Zone B",target_zone:"Central Area",probability:.63,eta_seconds:84,severity:"MEDIUM",reason:"58% density, trend +7%, movement toward Central Area."},
  {id:"c",source_zone:"Central Area",target_zone:"Exit C",probability:.40,eta_seconds:107,severity:"MEDIUM",reason:"41% density, trend +2%, movement toward Exit C."}
];
const now=()=>new Date().toISOString();
const summary=()=>({
  total_crowd_count:zones.reduce((s,z)=>s+z.current_count,0),
  active_zones:zones.length,
  risk_counts:{High:2,Medium:3,Low:3},
  active_alerts:2,
  zones,
  recent_alerts:[
    {id:1,created_at:now(),zone_name:"Gate A",severity:"CRITICAL",message:"High crowd density detected in Gate A."},
    {id:2,created_at:now(),zone_name:"Main Stage Area",severity:"WARNING",message:"Risk level increased due to crowd pressure."}
  ],
  recent_events:Array.from({length:6},(_,i)=>({id:i,crowd_count:620+i*95,timestamp:new Date(Date.now()-i*300000).toISOString()}))
});
export const localSimulator={
  summary:async()=>summary(),
  zones:async()=>zones,
  logs:async()=>[
    {id:1,created_at:now(),level:"INFO",source:"SYSTEM",message:"Local fallback simulation active"},
    {id:2,created_at:now(),level:"WARNING",source:"RISK_ENGINE",message:"Gate A pressure rising toward Zone B"}
  ],
  report:async()=>({period:"DAILY",metrics:{average_crowd_density:59.4,peak_crowd_count:2460,alert_count:12,high_risk_events:5,zone_utilization:58.7},zone_utilization:zones.map(z=>({name:z.name,utilization:z.density_score}))}),
  status:async()=>({running,speed:"normal"}),
  start:async()=>{running=true;return {running,speed:"normal"}},
  stop:async()=>{running=false;return {running,speed:"normal"}},
  reset:async()=>{running=false;return {running,speed:"normal"}},
  health:async()=>({status:"ok",mode:"local-simulation"}),
  predictiveFlow:async()=>({predictions:flows}),
  weather:async()=>({condition:"Light Rain",temperature_c:27,rain_mm:2.4,visibility_km:7.5,wind_kph:14,risk_modifier:.12,source:"local-fallback"}),
  schedule:async()=>({current_event:{event:"Main Performance",active:true,minutes_until:0,affected_zones:["Central Area","Gate A"],expected_surge:"high"},next_event:{event:"Closing Ceremony",minutes_until:45,affected_zones:["Central Area","Exit C"],expected_surge:"medium"}}),
  context:async()=>({zones,weather:{condition:"Light Rain",risk_modifier:.12}}),
  riskHistory:async()=>({history:[{time:"20:00",gate_a:46},{time:"20:05",gate_a:55},{time:"20:10",gate_a:64},{time:"20:15",gate_a:73},{time:"20:20",gate_a:82}]}),
  intelligenceReports:async()=>({reports:[
    {id:"R-101",type:"POLICE",message:"Crowd gathering near Gate A.",age_seconds:120},
    {id:"R-102",type:"CITIZEN",message:"Passage near Zone B is partially blocked.",age_seconds:75},
    {id:"R-103",type:"VOLUNTEER",message:"High density observed near Central Area.",age_seconds:35}
  ]}),
  incidents:async()=>({incidents:[
    {severity:"HIGH",title:"Gate A → Zone B",message:"81% congestion probability in 52 seconds."},
    {severity:"WATCH",title:"Weather context",message:"Rain may slow movement."}
  ]}),
  sop:async()=>({observation:"Gate A is creating downstream pressure toward Zone B.",trend:"82% density, trend +12%.",prediction:"Zone B has 81% predicted congestion probability in about 52 seconds.",recommendations:["Position trained volunteers near Zone B.","Monitor Gate A → Zone B.","Prepare alternate guidance if pressure continues."]}),
  simulation:async()=>({highest_risk_zone:"Gate A",summary:"Scenario indicates elevated downstream pressure.",predictions:flows}),
  operatorChat:async(message)=>({answer:/risk|danger|highest/i.test(message)?"Gate A currently has the highest density at 82% and is in High risk.":/move|congestion/i.test(message)?"Congestion is most likely to propagate from Gate A to Zone B in about 52 seconds (81% probability).":/weather|rain/i.test(message)?"Current weather is Light Rain at 27°C with +0.12 context risk.":"I can answer about current risk, movement, weather, schedule and recommendations.",source:"local-fallback"}),
  advisories:async()=>({advisories:advisoryState}),
  approve:async(id)=>{advisoryState=advisoryState.map(a=>a.id===id?{...a,status:"APPROVED"}:a);return {status:"APPROVED",id}},
  reject:async(id)=>{advisoryState=advisoryState.map(a=>a.id===id?{...a,status:"REJECTED"}:a);return {status:"REJECTED",id}}
};
