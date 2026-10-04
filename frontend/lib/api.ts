export const API=process.env.NEXT_PUBLIC_API_URL||'http://127.0.0.1:8000';
export async function request<T>(path:string,body?:unknown):Promise<T>{
  const response=await fetch(API+path,{method:body===undefined?'GET':'POST',headers:body===undefined?{}:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body),signal:AbortSignal.timeout(path==='/api/ingest/live'?45000:15000)});
  if(!response.ok){let message=`Request failed (${response.status})`;try{const data=await response.json();message=typeof data.detail==='string'?data.detail:message;}catch{}throw new Error(message);}
  return response.json();
}
