import os,pathlib,subprocess,shutil
home=pathlib.Path.home();label='com.asimfish.codex-vpn'
subprocess.run(['launchctl','bootout','gui/'+str(os.getuid())+'/'+label],capture_output=True)
(home/'Library/LaunchAgents'/f'{label}.plist').unlink(missing_ok=True)
app=home/'Applications/CodexVPN.app'
if app.exists():shutil.rmtree(app)
print('Removed CodexVPN app/login item. Private configuration and samples retained.')
