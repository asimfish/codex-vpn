import http.server,json,pathlib,threading,time,urllib.parse
from .core import load,collect_all,STATE

def serve(config,port):
    if not 1024<=port<=65535:raise ValueError('Choose a port from 1024 to 65535')
    stop=threading.Event()
    def poll():
        while not stop.is_set():
            start=time.monotonic()
            try:collect_all(load(config))
            except Exception:pass
            stop.wait(max(1,30-(time.monotonic()-start)))
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            if self.headers.get('Host') not in ['127.0.0.1:'+str(port),'localhost:'+str(port)]:self.send_error(403);return
            path=urllib.parse.urlparse(self.path).path
            if path=='/':body=(pathlib.Path(__file__).parent/'dashboard.html').read_bytes();mime='text/html; charset=utf-8'
            elif path=='/api/status':
                try:body=(STATE/'widget-snapshot.json').read_bytes()
                except FileNotFoundError:body=b'{"devices":[],"at":0,"target":"Waiting for sample","node":""}'
                mime='application/json'
            else:self.send_error(404);return
            self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; frame-ancestors 'none'");self.end_headers();self.wfile.write(body)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',port),Handler)
    threading.Thread(target=poll,daemon=True).start()
    print('LOCAL_DASHBOARD http://127.0.0.1:'+str(port),flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:stop.set();server.server_close()
