const BASE=import.meta.env.VITE_API_URL||"http://localhost:8000";
async function req(path,options={}){const r=await fetch(BASE+path,{headers:{"Content-Type":"application/json"},...options});if(!r.ok)throw new Error("API request failed");return r.json()}
export const api={
 summary:()=>req("/dashboard/summary"),zones:()=>req("/zones"),logs:(level,search)=>req("/logs?"+new URLSearchParams({...(level!=="ALL"?{level}:{}),...(search?{search}:{})})),
 report:p=>req("/reports/"+p),status:()=>req("/mock/status"),start:s=>req("/mock/start",{method:"POST",body:JSON.stringify({speed:s})}),
 stop:()=>req("/mock/stop",{method:"POST"}),reset:()=>req("/mock/reset",{method:"POST"})
};