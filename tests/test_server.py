import json,os,pathlib,socket,subprocess,sys,tempfile,time,unittest,urllib.request,urllib.error

class ServerTests(unittest.TestCase):
 def test_loopback_dashboard_and_host_boundary(self):
  with tempfile.TemporaryDirectory() as tmp:
   config=pathlib.Path(tmp)/'config.json';config.write_text(json.dumps({'node':'test','expected_ip':'203.0.113.10','devices':[{'id':'test','proxy_port':9,'controller_port':9,'selector_group':'test'}]}))
   with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
   proc=subprocess.Popen([sys.executable,'-m','codex_vpn','serve','--config',str(config),'--port',str(port)],env=dict(os.environ,HOME=tmp),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   op=urllib.request.build_opener(urllib.request.ProxyHandler({}));base='http://127.0.0.1:'+str(port)
   try:
    for _ in range(40):
     try:
      with op.open(base,timeout=1) as r:body=r.read();break
     except OSError:time.sleep(.1)
    else:self.fail('server did not start')
    self.assertIn(b'Egress Observatory',body)
    with op.open(base+'/api/status',timeout=2) as r:self.assertIn('devices',json.load(r))
    with self.assertRaises(urllib.error.HTTPError) as e:op.open(urllib.request.Request(base+'/api/status',headers={'Host':'attacker.example'}),timeout=2)
    self.assertEqual(e.exception.code,403)
   finally:proc.terminate();proc.wait(timeout=5)

if __name__=='__main__':unittest.main()
