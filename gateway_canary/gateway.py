"""Session-scoped Codex turn-state canary relay; no Clash or system proxy changes."""
import dataclasses,hashlib,json,threading,time,urllib.request
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
NORMAL={292:'individual-292',332:'team-332'}
SUSPECT={312:'individual-suspect-312',356:'team-suspect-356'}

@dataclasses.dataclass
class CanaryConfig:
    mode:str
    upstream:str
    ttl_seconds:int=3600

class StateStore:
    def __init__(self):self.lock=threading.Lock();self.state=None;self.captured_at=0;self.account='';self.model='';self.shape='';self.egress_profile=''
    def snapshot(self):
        with self.lock:return {'shape':self.shape,'captured_at':self.captured_at,'account':self.account,'model':self.model,'egress_profile':self.egress_profile}

class CanaryHandler:
    @staticmethod
    def _shape(value):return NORMAL.get(len(value)) or SUSPECT.get(len(value))
    @staticmethod
    def forward(cfg,state,model,account,body,headers,egress_profile='default'):
        outgoing=dict(headers);outgoing.pop('X-Codex-Turn-State',None)
        now=time.time();valid=state.state and now-state.captured_at<=cfg.ttl_seconds and state.account==account and state.model==model and state.egress_profile==egress_profile and state.shape in NORMAL.values()
        if cfg.mode=='inject' and valid:outgoing['X-Codex-Turn-State']=state.state
        request=urllib.request.Request(cfg.upstream,data=body,headers=outgoing,method='POST')
        with urllib.request.urlopen(request,timeout=90) as response:
            response_body=response.read();response_headers={k:v for k,v in response.headers.items() if k.lower()!='x-codex-turn-state'}
            turn=response.headers.get('X-Codex-Turn-State','');shape=CanaryHandler._shape(turn)
            if cfg.mode in ('observe','inject') and turn and shape in NORMAL.values():
                with state.lock:
                    state.state=turn;state.captured_at=now;state.account=account;state.model=model;state.shape=shape;state.egress_profile=egress_profile
            return response.status,response_headers,response_body

def serve(config_path,listen):
    cfg=json.loads(open(config_path).read());config=CanaryConfig(cfg.get('mode','off'),cfg['upstream_url'],int(cfg.get('ttl_seconds',3600)));state=StateStore()
    if config.mode=='off':raise SystemExit('Canary is disabled (mode=off)')
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            try:
                body=self.rfile.read(int(self.headers.get('Content-Length','0')));data=json.loads(body or b'{}');model=str(data.get('model',''));authorization=self.headers.get('Authorization','');account=self.headers.get('X-Canary-Account') or hashlib.sha256(authorization.encode()).hexdigest()[:16];result=CanaryHandler.forward(config,state,model,account,body,dict(self.headers),self.headers.get('X-Canary-Egress','default'));self.send_response(result[0]);
                for k,v in result[1].items():self.send_header(k,v)
                self.end_headers();self.wfile.write(result[2])
            except Exception as e:self.send_error(502,'canary upstream failure')
        def do_GET(self):
            if self.path=='/health':self.send_response(200);self.end_headers();self.wfile.write(json.dumps({'mode':config.mode,'state':state.snapshot()}).encode());return
            self.send_error(404)
        def log_message(self,*a):pass
    server=ThreadingHTTPServer((listen[0],listen[1]),Handler);print('CANARY_LISTEN '+str(listen[0])+':'+str(listen[1]),flush=True);server.serve_forever()
