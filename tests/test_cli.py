import json,os,pathlib,subprocess,sys,tempfile,unittest

class CLITests(unittest.TestCase):
 def test_fresh_init_and_remote_runner(self):
  with tempfile.TemporaryDirectory() as tmp:
   env=dict(os.environ,HOME=tmp)
   r=subprocess.run([sys.executable,'-m','codex_vpn','init'],env=env,capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr)
   config=pathlib.Path(tmp)/'.config/codex-vpn/config.json';self.assertTrue(config.exists())
   before=config.read_bytes();r=subprocess.run([sys.executable,'-m','codex_vpn','init'],env=env,capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0);self.assertEqual(config.read_bytes(),before)
   r=subprocess.run([sys.executable,'-m','codex_vpn','agent-install'],env=env,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
   runner=pathlib.Path(tmp)/'.local/share/codex-vpn/agent.py'
   r=subprocess.run([sys.executable,str(runner),'--help'],env=env,capture_output=True,text=True,cwd=tmp);self.assertEqual(r.returncode,0,r.stderr)

if __name__=='__main__':unittest.main()
