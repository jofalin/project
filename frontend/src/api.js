const BASE=import.meta.env.VITE_API_URL||"http://localhost:8000";
async function req(path,options={}){const r=await fetch(BASE+path,{headers:{"Content-Type":"application/json"},...options});if(!r.ok)throw new Error("API request failed");return r.json()}
export const api={
 summary:()=>req("/dashboard/summary"),
 zones:()=>req("/zones"),
 logs:(level,search)=>req("/logs?"+new URLSearchParams({...(level!=="ALL"?{level}:{}),...(search?{search}:{})})),
 report:(p,start,end)=>req("/reports/"+p+"?"+new URLSearchParams({...(start?{start_date:start}:{}),...(end?{end_date:end}:{})})),
 status:()=>req("/mock/status"),
 start:s=>req("/mock/start",{method:"POST",body:JSON.stringify({speed:s})}),
 stop:()=>req("/mock/stop",{method:"POST"}),
 reset:()=>req("/mock/reset",{method:"POST"}),
 health:()=>req("/api/health"),
 predictiveFlow:()=>req("/api/predictive-flow"),
 weather:()=>req("/api/weather"),
 schedule:()=>req("/api/schedule"),
 context:()=>req("/api/context"),
 riskHistory:()=>req("/api/risk-history"),
 intelligenceReports:()=>req("/api/reports"),
 incidents:()=>req("/api/incidents"),
 sop:()=>req("/api/sop"),
 simulation:payload=>req("/api/simulation",{method:"POST",body:JSON.stringify(payload)}),
 operatorChat:(message,history=[])=>req("/api/operator-chat",{method:"POST",body:JSON.stringify({message,history})}),
 advisories:()=>req("/api/advisories"),
 approve:id=>req("/api/advisories/"+id+"/approve",{method:"POST"}),
 reject:id=>req("/api/advisories/"+id+"/reject",{method:"POST"})
};