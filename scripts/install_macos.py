"""Build an isolated app bundle; never modifies any proxy or Codex settings."""
import argparse,os,pathlib,plistlib,shutil,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--dest',default=str(pathlib.Path.home()/'Applications/CodexVPN.app'));p.add_argument('--no-autostart',action='store_true');p.add_argument('--no-start',action='store_true');a=p.parse_args()
if sys.platform!='darwin':raise SystemExit('Native widget requires macOS; use python3 -m codex_vpn serve on Linux.')
B=pathlib.Path(__file__).resolve().parent.parent;app=pathlib.Path(a.dest).expanduser();exe=app/'Contents/MacOS/CodexVPN';resources=app/'Contents/Resources';resources.mkdir(parents=True,exist_ok=True);exe.parent.mkdir(parents=True,exist_ok=True)
subprocess.run(['xcrun','swiftc',str(B/'Sources/main.swift'),'-o',str(exe),'-framework','AppKit','-framework','SwiftUI'],check=True)
shutil.copytree(B/'codex_vpn',resources/'codex_vpn',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
shutil.copy2(B/'scripts/collector.py',resources/'collector.py');shutil.copy2(B/'docs/Guide.html',resources/'Guide.html')
info={'CFBundleIdentifier':'com.asimfish.codex-vpn','CFBundleName':'CodexVPN','CFBundleDisplayName':'Codex VPN','CFBundleExecutable':'CodexVPN','CFBundlePackageType':'APPL','CFBundleShortVersionString':'0.1.0','CFBundleVersion':'1','LSUIElement':True,'LSMinimumSystemVersion':'14.0','NSHighResolutionCapable':True}
(app/'Contents/Info.plist').write_bytes(plistlib.dumps(info))
# Strip only Finder metadata from this generated app; preserve quarantine attributes.
for attr in ['com.apple.FinderInfo','com.apple.ResourceFork']:
    subprocess.run(['/usr/bin/xattr','-dr',attr,str(app)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run(['codesign','--force','--deep','--sign','-',str(app)],check=True)
if not a.no_autostart:
    label='com.asimfish.codex-vpn';target='gui/'+str(os.getuid());plist=pathlib.Path.home()/'Library/LaunchAgents'/f'{label}.plist';plist.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['launchctl','bootout',target+'/'+label],capture_output=True)
    plist.write_bytes(plistlib.dumps({'Label':label,'ProgramArguments':[str(exe)],'RunAtLoad':not a.no_start,'LimitLoadToSessionType':'Aqua','ProcessType':'Interactive'}));plist.chmod(0o600)
    subprocess.run(['launchctl','bootstrap',target,str(plist)],check=True)
elif not a.no_start:subprocess.run(['open',str(app)],check=True)
print('APP_INSTALLED '+str(app))
