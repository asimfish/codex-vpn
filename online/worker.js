import {isIP} from 'node:net';
const json=(value,status=200)=>Response.json(value,{status,headers:{'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
export default {async fetch(request,env){
 const url=new URL(request.url);
 if(request.method!=='GET')return json({error:'Method not allowed'},405);
 if(url.pathname==='/')return new Response(`<!doctype html><meta charset="utf-8"><title>Codex VPN online checks</title><style>body{max-width:850px;margin:50px auto;padding:20px;font:16px/1.8 system-ui;background:#0d1924;color:#dde7ef}input,button{padding:12px}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><h1>Codex VPN · Online egress checks</h1><p>Use your device token with /check. This proves the HTTPS request source, not model traffic.</p><input id="token" type="password" placeholder="Administrator token" autocomplete="off"><button id="load">Load recent checks</button><pre id="out">No credentials are stored in your browser.</pre><script>document.querySelector('#load').onclick=async()=>{const r=await fetch('/history',{headers:{Authorization:'Bearer '+document.querySelector('#token').value}});document.querySelector('#out').textContent=JSON.stringify(await r.json(),null,2)}</script>`,{headers:{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store','Content-Security-Policy':"default-src 'none'; connect-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; frame-ancestors 'none'"}});
 if(url.pathname==='/history'){
  if(!env.ADMIN_TOKEN||request.headers.get('authorization')!=='Bearer '+env.ADMIN_TOKEN)return json({error:'Unauthorized'},401);
  const {results}=await env.DB.prepare('SELECT * FROM checks ORDER BY received_at DESC LIMIT 100').all();return json({checks:results});
 }
 if(url.pathname!=='/check')return json({error:'Not found'},404);
 let tokens;try{tokens=JSON.parse(env.DEVICE_TOKENS||'{}')}catch{return json({error:'Configuration unavailable'},503)}
 const id=request.headers.get('x-device-id')||'';
 if(!/^[a-zA-Z0-9_-]{1,48}$/.test(id)||!Object.hasOwn(tokens,id)||!tokens[id]||request.headers.get('authorization')!=='Bearer '+tokens[id])return json({error:'Unauthorized'},401);
 // Cloudflare's ingress overwrites this header. Never use client X-Forwarded-For.
 const ip=request.headers.get('cf-connecting-ip');
 const valid=ip&&isIP(ip)&&!['2a06:98c0:3600::103','2a06:98c0::103'].includes(ip.toLowerCase());
 const now=Date.now(),record={test_id:crypto.randomUUID(),device:id,received_at:now,observed_ip:valid?ip:null,expected_ip:env.EXPECTED_IP,result:!valid||!env.EXPECTED_IP?'UNVERIFIED':ip===env.EXPECTED_IP?'MATCH':'MISMATCH'};
 const last=await env.DB.prepare('SELECT received_at FROM checks WHERE device=? ORDER BY received_at DESC LIMIT 1').bind(id).first();
 if(last&&now-last.received_at<3000)return json({error:'Retry after 3 seconds'},429);
 await env.DB.batch([env.DB.prepare('INSERT INTO checks VALUES(?,?,?,?,?,?)').bind(record.test_id,id,now,record.observed_ip,record.expected_ip,record.result),env.DB.prepare('DELETE FROM checks WHERE received_at < ?').bind(now-86400000)]);
 return json({...record,scope:'This HTTPS request only; not proof of Codex model traffic'});
}};
