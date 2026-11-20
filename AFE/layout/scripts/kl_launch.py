# kl_launch.py: started by kl.sh inside KLayout; runs $KL_SCRIPT with the kit directory on sys.path and the name=value arguments of kl.sh as globals.
import os, sys, runpy, traceback
kit, script = os.environ['KL_KIT'], os.environ['KL_SCRIPT']
for p in (os.path.dirname(script), kit):
    if p not in sys.path:
        sys.path.insert(0, p)
g = {}
for kv in os.environ.get('KL_ARGS', '').split('\n'):
    if '=' in kv:
        a, b = kv.split('=', 1)
        g[a.strip()] = b
try:
    runpy.run_path(script, init_globals=g, run_name='__main__')
except SystemExit as e:
    if e.code not in (None, 0):
        print('kl.sh: %s exited with %s' % (script, e.code))
        raise
except Exception:
    traceback.print_exc()
    print('kl.sh: FAILED %s' % script)
    sys.exit(1)
