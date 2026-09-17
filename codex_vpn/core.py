import concurrent.futures,ipaddress,json,os,pathlib,re,shlex,subprocess,time,urllib.parse,urllib.request

CONFIG=pathlib.Path.home()/'.config/codex-vpn/config.json'
STATE=pathlib.Path.home()/'.local/share/codex-vpn'

def atomic(path,value):
    path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    tmp=path.with_name(path.name+'.'+str(os.getpid())+'.tmp')
    fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as f:json.dump(value,f,ensure_ascii=False,indent=2)
    os.replace(tmp,path)

def load(path=CONFIG):
    c=json.loads(pathlib.Path(path).expanduser().read_text())
    ipaddress.ip_address(c['expected_ip'])
    if not c.get('node') or not c.get('devices'):raise ValueError('node and devices are required')
    ids=set()
    for d in c['devices']:
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,48}',d['id']) or d['id'] in ids:raise ValueError('Invalid or duplicate device ID')
        ids.add(d['id'])
        for k in ['proxy_port','controller_port']:
            if type(d.get(k)) is not int or not 1<=d[k]<=65535:raise ValueError('Invalid '+k)
        if d.get('ssh') and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',d['ssh']):raise ValueError('Use an existing SSH alias')
        if d.get('ssh') and not re.fullmatch(r'/[A-Za-z0-9_./-]+',d.get('remote_home','')):raise ValueError('Absolute remote_home required')
        if '..' in d.get('remote_home','').split('/'):raise ValueError('Unsafe remote_home')
    return c

def controller(device,path):
    secret=os.environ.get(device.get('controller_secret_env','CODEX_VPN_CONTROLLER_SECRET'),'')
    if device.get('controller_secret_file'):
        secret=pathlib.Path(device['controller_secret_file']).expanduser().read_text().strip()
    req=urllib.request.Request('http://127.0.0.1:'+str(device['controller_port'])+path,headers={'Authorization':'Bearer '+secret})
    op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with op.open(req,timeout=8) as r:return json.load(r)

def probe(port,url):
    cmd=['curl','-4','-fsS','--max-time','15','--noproxy','','--proxy','http://127.0.0.1:'+str(port),url,'-w','\n%{time_total}']
    r=subprocess.run(cmd,capture_output=True,text=True,timeout=18)
    if r.returncode:raise RuntimeError('HTTPS probe failed')
    body,seconds=r.stdout.rsplit('\n',1)
    ip=dict(line.split('=',1) for line in body.splitlines() if '=' in line).get('ip') if 'cdn-cgi/trace' in url else body.strip()
    return str(ipaddress.ip_address(ip)),round(float(seconds)*1000)

def classify(s,c,now):
    age=now-s.get('checked_at',0)
    if age < -10000 or age > 100000:return 'stale'
    if any(ip and ip!=c['expected_ip'] for ip in [s.get('ip'),s.get('secondary')]):return 'mismatch'
    if s.get('node') and s['node']!=c['node']:return 'mismatch'
    if s.get('error') or not s.get('ip') or not s.get('secondary'):return 'error'
    if not s.get('node'):return 'unknown'
    return 'ok'

def sample(c,d):
    from .evidence import collect
    errors=[];ips=[];latency=None;node=None;nodes=[]
    for url in ['https://www.cloudflare.com/cdn-cgi/trace','https://api.ipify.org']:
        try:ip,ms=probe(d['proxy_port'],url);ips.append(ip);latency=ms if latency is None else latency
        except Exception:ips.append(None);errors.append('出口检测失败')
    api=lambda path:controller(d,path)
    try:
        group=api('/proxies/'+urllib.parse.quote(d['selector_group'],safe=''))
        node=group.get('now')
        # Do not confuse undated native health cache with a fresh measurement.
        for name in c.get('nodes',[c['node']]):
            nodes.append({'name':name,'delay':None}) # Never present an undated cache as fresh.
    except Exception:errors.append('控制接口或代理组不可用')
    settings={'proxy_port':d['proxy_port'],'node':c['node'],'codex_hosts':c.get('codex_hosts',['openai.com','chatgpt.com'])}
    ev=collect(api,settings)
    if ev.get('connections',0)>ev.get('matched_connections',0):verdict='路径不一致'
    elif any(e.get('source')=='socket-pid' and e.get('node_match') for e in ev.get('evidence',[])):verdict='PID连接已观测'
    elif ev.get('matched_connections'):verdict='内核路径已观测'
    elif ev.get('env_matched'):verdict='仅环境配置'
    else:verdict='未捕获连接'
    s={'id':d['id'],'name':d.get('name',d['id']),'ip':ips[0] or '','secondary':ips[1] or '','node':node or '', 'checked_at':int(time.time()*1000),'delay':latency,'codex':verdict,'error':'; '.join(errors) or None,'nodes':nodes,'proxy_port':d['proxy_port'],'controller_port':d['controller_port'],'evidence':ev}
    s['status']=classify(s,c,int(time.time()*1000));return s

def remote_sample(c,d):
    command=['python3',d['remote_home']+'/.local/share/codex-vpn/agent.py','sample','--device',d['id']]
    r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','-o','ServerAliveInterval=5','-o','ServerAliveCountMax=1',d['ssh'],shlex.join(command)],capture_output=True,text=True,timeout=65)
    if r.returncode:raise RuntimeError('SSH sample unavailable')
    s=json.loads(r.stdout)
    if s.get('id')!=d['id']:raise ValueError('Remote ID mismatch')
    return s

def collect_all(c):
    def one(d):
        try:
            s=remote_sample(c,d) if d.get('ssh') else sample(c,d)
            s['name']=d.get('name',d['id']);s['status']=classify(s,c,int(time.time()*1000));return s
        except Exception:return {'id':d['id'],'name':d.get('name',d['id']),'ip':'','secondary':'','node':'','status':'unknown','checked_at':0,'delay':None,'codex':'未捕获连接','nodes':[],'proxy_port':d['proxy_port'],'controller_port':d['controller_port'],'error':'采集失败，检查 SSH / 远端安装'}
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(4,len(c['devices']))) as p:rows=list(p.map(one,c['devices']))
    payload={'at':int(time.time()*1000),'target':c['expected_ip'],'node':c['node'],'devices':rows}
    atomic(STATE/'widget-snapshot.json',payload);return payload
