import json,pathlib,tempfile,unittest
from unittest.mock import patch
from codex_vpn.core import atomic,load,classify,sample
from codex_vpn.evidence import socket_key

class CoreTests(unittest.TestCase):
 def test_private_config(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp)/'c.json';atomic(p,{'a':1});self.assertEqual(p.stat().st_mode&0o777,0o600);self.assertEqual(json.loads(p.read_text()),{'a':1})
 def test_validation(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp)/'c.json';c={'node':'node','expected_ip':'203.0.113.10','devices':[{'id':'local','proxy_port':7890,'controller_port':9090}]};atomic(p,c);self.assertEqual(len(load(p)['devices']),1)
   c['devices'][0]['ssh']='-oBad';atomic(p,c)
   with self.assertRaises(ValueError):load(p)
 def test_status(self):
  c={'node':'node','expected_ip':'203.0.113.10'};s={'checked_at':1000000,'node':'node','ip':'203.0.113.10','secondary':'203.0.113.10'}
  self.assertEqual(classify(s,c,1000000),'ok');self.assertEqual(classify(s,c,1100001),'stale')
  self.assertEqual(classify(dict(s,secondary='203.0.113.11'),c,1000000),'mismatch')
  self.assertEqual(classify(dict(s,error='probe failed'),c,1000000),'error')
 def test_socket_normalization(self):self.assertEqual(socket_key('[::ffff:127.0.0.1]:1234'),('127.0.0.1','1234'))
 def test_sample_does_not_promote_env_to_connection(self):
  with patch('codex_vpn.core.probe',return_value=('203.0.113.10',123)),patch('codex_vpn.core.controller',return_value={'now':'node'}),patch('codex_vpn.evidence.collect',return_value={'env_matched':1}):
   s=sample({'expected_ip':'203.0.113.10','node':'node'},{'id':'local','proxy_port':7890,'controller_port':9090,'selector_group':'group'})
   self.assertEqual(s['status'],'ok');self.assertEqual(s['codex'],'仅环境配置')

if __name__=='__main__':unittest.main()
