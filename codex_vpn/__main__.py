import argparse,json,os,pathlib,shutil,sys,time
from .core import CONFIG,STATE,atomic,load,sample,collect_all

def main():
    p=argparse.ArgumentParser(prog='codex-vpn',description='Read-only proxy and Codex connection monitor')
    p.add_argument('command',choices=['init','sample','collect','watch','serve','agent-install','online-check'])
    p.add_argument('--config',default=str(CONFIG));p.add_argument('--device');p.add_argument('--loop',action='store_true');p.add_argument('--seconds',type=int,default=60);p.add_argument('--pid',type=int);p.add_argument('--port',type=int,default=8766);p.add_argument('--explicit-proxy',action='store_true');a=p.parse_args()
    if a.command=='init':
        path=pathlib.Path(a.config).expanduser()
        if path.exists():raise SystemExit('Config exists; left unchanged: '+str(path))
        atomic(path,{'node':'YOUR_NODE_NAME','expected_ip':'203.0.113.10','nodes':['YOUR_NODE_NAME'],'devices':[{'id':'local','name':'My computer','proxy_port':7890,'controller_port':9090,'selector_group':'YOUR_SELECTOR_GROUP','controller_secret_env':'CODEX_VPN_CONTROLLER_SECRET'}]})
        print('Created private config: '+str(path));print('Replace placeholder IP, node and selector group before sampling.');return
    if a.command=='agent-install':
        dest=STATE/'codex_vpn';STATE.mkdir(parents=True,exist_ok=True,mode=0o700)
        shutil.copytree(pathlib.Path(__file__).parent,dest,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
        (STATE/'agent.py').write_text('from codex_vpn.__main__ import main\nmain()\n')
        print('AGENT_INSTALLED '+str(STATE/'agent.py'));return
    c=load(a.config)
    d=next((d for d in c['devices'] if d['id']==a.device),None) if a.device else next((d for d in c['devices'] if not d.get('ssh')),None)
    if a.command in ['sample','watch','online-check'] and d is None:raise SystemExit('Select a local device with --device ID')
    if a.command=='sample':print(json.dumps(sample(c,d),ensure_ascii=False,indent=2));return
    if a.command=='collect':
        parent=os.getppid()
        while True:
            start=time.monotonic();result=collect_all(load(a.config))
            if not a.loop:print(json.dumps(result,ensure_ascii=False,indent=2));return
            if os.getppid()!=parent:return
            time.sleep(max(1,30-(time.monotonic()-start)))
    if a.command=='serve':
        from .server import serve
        serve(a.config,a.port);return
    if a.command=='online-check':
        import urllib.request
        target=c.get('online',{});url=target.get('url','')
        if not url.startswith('https://'):raise SystemExit('online.url must be your deployed HTTPS /check endpoint')
        token=os.environ.get(target.get('token_env','CODEX_VPN_CHECK_TOKEN'),'')
        if not token:raise SystemExit('Set the online token environment variable')
        request=urllib.request.Request(url,headers={'Authorization':'Bearer '+token,'X-Device-Id':d['id']})
        op=urllib.request.build_opener(urllib.request.ProxyHandler({'https':'http://127.0.0.1:'+str(d['proxy_port'])})) if a.explicit_proxy else urllib.request.build_opener()
        with op.open(request,timeout=25) as r:result=json.load(r)
        print(json.dumps(result,indent=2));raise SystemExit(0 if result.get('result')=='MATCH' else 2)
    if a.command=='watch':
        from .core import controller
        from .evidence import collect
        network=sample(c,d)
        if network['status']!='ok':print(json.dumps(network,ensure_ascii=False));raise SystemExit(2)
        print('Send a real request in the target Codex now.',flush=True)
        until=time.monotonic()+max(2,min(a.seconds,300));seen=False;wrong=False
        while time.monotonic()<until:
            e=collect(lambda path:controller(d,path),{'proxy_port':d['proxy_port'],'node':c['node']})
            records=[r for r in e.get('evidence',[]) if not a.pid or r.get('pid')==a.pid]
            if records:seen=True;wrong|=any(not r['node_match'] for r in records);print(json.dumps(records,ensure_ascii=False),flush=True)
            time.sleep(2)
        print('CODEX_PATH_MISMATCH' if wrong else 'CODEX_PATH_OBSERVED' if seen else 'CODEX_UNVERIFIED')
        raise SystemExit(2 if wrong else 0 if seen else 3)
if __name__=='__main__':main()
