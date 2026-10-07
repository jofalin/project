import {localSimulator} from "./localSimulator";

const BASE = String(import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/,"");
const API_KEY = String(import.meta.env.VITE_API_KEY || "");
const FAILURE_LIMIT = 3;
const OPEN_MS = 20000;
const TIMEOUT_MS = 2500;

let failures = 0;
let circuitOpenUntil = 0;

export const apiClientState = {
  baseUrl: BASE,
  liveConfigured: Boolean(BASE),
  circuitOpen: () => Date.now() < circuitOpenUntil,
  resetCircuit: () => { failures = 0; circuitOpenUntil = 0; }
};

function recordSuccess(){ failures = 0; circuitOpenUntil = 0; }
function recordFailure(){
  failures += 1;
  if(failures >= FAILURE_LIMIT) circuitOpenUntil = Date.now() + OPEN_MS;
}

async function liveRequest(path, options={}){
  const controller = new AbortController();
  const timeout = setTimeout(()=>controller.abort(), TIMEOUT_MS);
  try{
    const headers = {"Content-Type":"application/json", ...(API_KEY ? {"X-API-Key":API_KEY}:{}), ...(options.headers||{})};
    const response = await fetch(BASE + path, {...options,headers,signal:controller.signal});
    if(!response.ok) throw new Error("HTTP "+response.status);
    const data = await response.json();
    recordSuccess();
    return data;
  }finally{ clearTimeout(timeout); }
}

async function withFallback(path, options, fallback){
  if(!BASE || Date.now() < circuitOpenUntil) return fallback();
  try{return await liveRequest(path,options);}
  catch(error){recordFailure();return fallback(error);}
}

export const api = {
  summary:()=>withFallback("/dashboard/summary",{},localSimulator.summary),
  zones:()=>withFallback("/zones",{},localSimulator.zones),
  logs:(level,search)=>withFallback("/logs?"+new URLSearchParams({...(level&&level!=="ALL"?{level}:{}),...(search?{search}:{})}),{},localSimulator.logs),
  report:(period,start,end)=>withFallback("/reports/"+period,{},localSimulator.report),
  status:()=>withFallback("/mock/status",{},localSimulator.status),
  start:s=>withFallback("/mock/start",{method:"POST",body:JSON.stringify({speed:s})},localSimulator.start),
  stop:()=>withFallback("/mock/stop",{method:"POST"},localSimulator.stop),
  reset:()=>withFallback("/mock/reset",{method:"POST"},localSimulator.reset),
  health:()=>withFallback("/healthz",{},localSimulator.health),
  predictiveFlow:()=>withFallback("/api/v1/predict/propagation",{},localSimulator.predictiveFlow),
  weather:()=>withFallback("/api/weather",{},localSimulator.weather),
  schedule:()=>withFallback("/api/schedule",{},localSimulator.schedule),
  context:()=>withFallback("/api/context",{},localSimulator.context),
  riskHistory:()=>withFallback("/api/risk-history",{},localSimulator.riskHistory),
  intelligenceReports:()=>withFallback("/api/reports",{},localSimulator.intelligenceReports),
  incidents:()=>withFallback("/api/incidents",{},localSimulator.incidents),
  sop:()=>withFallback("/api/sop",{},localSimulator.sop),
  simulation:payload=>withFallback("/api/simulation",{method:"POST",body:JSON.stringify(payload)},localSimulator.simulation),
  operatorChat:(message,history=[])=>withFallback("/api/operator-chat",{method:"POST",body:JSON.stringify({message,history})},()=>localSimulator.operatorChat(message,history)),
  advisories:()=>withFallback("/api/advisories",{},localSimulator.advisories),
  approve:id=>withFallback("/api/advisories/"+id+"/approve",{method:"POST"},()=>localSimulator.approve(id)),
  reject:id=>withFallback("/api/advisories/"+id+"/reject",{method:"POST"},()=>localSimulator.reject(id))
};
