import pathlib,sys,os,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from codex_vpn.core import collect_all,load
parent=os.getppid()
while parent!=1 and os.getppid()==parent:
    start=time.monotonic()
    try:collect_all(load())
    except Exception:pass
    time.sleep(max(1,30-(time.monotonic()-start)))
