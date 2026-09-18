import json,threading,time,unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from .gateway import StateStore,CanaryHandler,CanaryConfig

class Upstream(BaseHTTPRequestHandler):
    last_turn=''
    def do_POST(self):
        Upstream.last_turn=self.headers.get('X-Codex-Turn-State','');body=b'{"ok":true}';self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.send_header('X-Codex-Turn-State','x'*292);self.end_headers();self.wfile.write(body)
    def log_message(self,*a):pass

class CanaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.up=ThreadingHTTPServer(('127.0.0.1',0),Upstream);threading.Thread(target=cls.up.serve_forever,daemon=True).start()
    @classmethod
    def tearDownClass(cls):cls.up.shutdown()
    def test_observe_captures_normal_shape_without_injecting(self):
        state=StateStore();cfg=CanaryConfig('observe',f'http://127.0.0.1:{self.up.server_port}',60)
        status,headers,body=CanaryHandler.forward(cfg,state,'gpt-5','acct-a',b'{}',{})
        self.assertEqual(status,200);self.assertEqual(state.snapshot()['shape'],'individual-292');self.assertNotIn('X-Codex-Turn-State',headers)
    def test_inject_requires_same_account_and_model_and_ttl(self):
        state=StateStore();cfg=CanaryConfig('observe',f'http://127.0.0.1:{self.up.server_port}',60)
        CanaryHandler.forward(cfg,state,'gpt-5','acct-a',b'{}',{});cfg.mode='inject'
        CanaryHandler.forward(cfg,state,'gpt-5','acct-a',b'{}',{});self.assertEqual(Upstream.last_turn,'x'*292)
        self.assertNotIn('X-Codex-Turn-State',CanaryHandler.forward(cfg,state,'gpt-5.1','acct-a',b'{}',{})[1])
        self.assertNotIn('X-Codex-Turn-State',CanaryHandler.forward(cfg,state,'gpt-5','acct-b',b'{}',{})[1])
        state.captured_at=time.time()-61;self.assertNotIn('X-Codex-Turn-State',CanaryHandler.forward(cfg,state,'gpt-5','acct-a',b'{}',{})[1])

if __name__=='__main__':unittest.main()
