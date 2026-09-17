"""Sanitized read-only Codex process/socket/Clash correlation."""
import os,pathlib,re,subprocess,sys,time,ipaddress

def socket_key(address,port=None):
    if port is None:address,port=address.rsplit(':',1)
    address=address.strip('[]').split('%',1)[0]
    ip=ipaddress.ip_address(address);ip=getattr(ip,'ipv4_mapped',None) or ip
    return str(ip),str(port)

def collect(api,settings):
    pids=set();matched=0;unreadable=0;bypass=0;ports={};inspection='unavailable'
    proxy_port=str(settings['proxy_port'])
    if pathlib.Path('/proc').exists():
        inspection='linux-proc'
        for p in pathlib.Path('/proc').glob('[0-9]*'):
            try:
                if p.stat().st_uid!=os.getuid() or (p/'comm').read_text().strip()!='codex':continue
                pid=int(p.name);pids.add(pid)
                try:
                    env=dict(x.split(b'=',1) for x in (p/'environ').read_bytes().split(b'\0') if b'=' in x)
                    values=[env.get(k,b'').decode(errors='replace') for k in [b'HTTPS_PROXY',b'https_proxy',b'ALL_PROXY',b'all_proxy']]
                    exclusions=(env.get(b'NO_PROXY',b'')+b','+env.get(b'no_proxy',b'')).decode(errors='replace').lower().split(',')
                    risky=any(v.strip() in ['*','0.0.0.0/0','::/0'] or any(h==v.strip().lstrip('*.') or h.endswith('.'+v.strip().lstrip('*.')) for h in ['api.openai.com','chatgpt.com']) for v in exclusions if v.strip())
                    bypass+=int(risky)
                    matched+=int(not risky and any(v in ['http://127.0.0.1:'+proxy_port,'socks5://127.0.0.1:'+proxy_port] for v in values))
                except Exception:unreadable+=1
            except Exception:pass
        try:
            lines=subprocess.run(['ss','-Htnp'],capture_output=True,text=True,timeout=3).stdout.splitlines();inspection='linux-proc+ss'
            for line in lines:
                parts=line.split()
                if len(parts)<5:continue
                found=re.findall(r'pid=(\d+)',line)
                own={int(p) for p in found if int(p) in pids}
                if own:ports.setdefault(socket_key(parts[3]),set()).update(own)
        except Exception:pass
    elif sys.platform=='darwin':
        inspection='macos-core-metadata'
        try:
            lines=subprocess.run(['ps','-axo','pid=,comm='],capture_output=True,text=True,timeout=3).stdout.splitlines()
            for line in lines:
                parts=line.strip().split(None,1)
                if len(parts)==2 and (os.path.basename(parts[1]).lower()=='codex' or '/codex.app/' in parts[1].lower()):pids.add(int(parts[0]))
            if pids:
                data=subprocess.run(['lsof','-nP','-a','-p',','.join(map(str,sorted(pids)[:80])),'-iTCP','-sTCP:ESTABLISHED','-Fpn'],capture_output=True,text=True,timeout=4).stdout
                current=None
                for line in data.splitlines():
                    if line.startswith('p'):current=int(line[1:])
                    if line.startswith('n') and '->' in line:
                        local,peer=line[1:].split('->',1)
                        ports.setdefault(socket_key(local),set()).add(current)
                inspection='macos-lsof+core'
        except Exception:pass
    observed=[]
    hosts=settings.get('codex_hosts',['openai.com','chatgpt.com','oaistatic.com','oaiusercontent.com'])
    try:
        for connection in (api('/connections').get('connections') or []):
            m=connection.get('metadata',{});host=str(m.get('host','')).lower()
            if not any(host==h or host.endswith('.'+h) for h in hosts):continue
            try:candidates=ports.get(socket_key(str(m.get('sourceIP','')),m.get('sourcePort')),set())
            except ValueError:candidates=set()
            pid=next(iter(candidates)) if len(candidates)==1 else None
            process=str(m.get('process','')).lower();path=str(m.get('processPath','')).lower()
            process_match=process.startswith('codex') or os.path.basename(path).startswith('codex') or '/codex.app/' in path
            if not pid and not process_match:continue
            uid=m.get('uid')
            if uid not in [None,'',-1,'-1']:
                try:
                    if int(uid)!=os.getuid() and not pid:continue
                except (TypeError,ValueError):pass
            chain=[str(x)[:100] for x in connection.get('chains',[])][:12]
            observed.append({'pid':pid,'host':host[:100],'chains':chain,'source':'socket-pid' if pid else 'core-process','node_match':settings['node'] in chain})
    except Exception:pass
    good=sum(x['node_match'] for x in observed)
    if observed:verdict='已观测的 Codex 连接走目标节点' if good==len(observed) else '发现 Codex 连接与目标节点不一致'
    elif matched:verdict='代理环境已设置，尚无活动连接证据'
    else:verdict='尚未证实 Codex 的实际连接路径'
    return {'processes':len(pids),'env_matched':matched,'env_unreadable':unreadable,'env_bypass_risk':bypass,'inspection':inspection,'connections':len(observed),'matched_connections':good,'checked_at':int(time.time()*1000),'evidence':observed[:20],'verdict':verdict}
