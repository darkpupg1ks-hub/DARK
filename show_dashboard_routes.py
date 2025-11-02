import importlib.util
import importlib.machinery
import sys
import os
from types import ModuleType
from flask import Flask

base_dir = os.path.dirname(__file__)
bp_path = os.path.join(base_dir, 'app', 'blueprints', 'dashboard.py')

# Ensure a minimal 'app' and 'app.blueprints' package exist in sys.modules
app_pkg = ModuleType('app')
app_pkg.__path__ = [os.path.join(base_dir, 'app')]
sys.modules['app'] = app_pkg

blueprints_pkg = ModuleType('app.blueprints')
blueprints_pkg.__path__ = [os.path.join(base_dir, 'app', 'blueprints')]
sys.modules['app.blueprints'] = blueprints_pkg

# Provide a minimal 'app.services.supabase_client' to satisfy relative imports
services_pkg = ModuleType('app.services')
services_pkg.__path__ = [os.path.join(base_dir, 'app', 'services')]
sys.modules['app.services'] = services_pkg

sup_mod = ModuleType('app.services.supabase_client')
def dummy_get_supabase():
    class Dummy:
        def table(self, *a, **k):
            class Q:
                def select(self, *a, **k):
                    return self
                def order(self, *a, **k):
                    return self
                def execute(self):
                    return type('R', (), {'data': []})()
            return Q()
    return Dummy()

sup_mod.get_supabase = dummy_get_supabase
sys.modules['app.services.supabase_client'] = sup_mod

spec = importlib.util.spec_from_file_location('app.blueprints.dashboard', bp_path)
dashboard_mod = importlib.util.module_from_spec(spec)
sys.modules['app.blueprints.dashboard'] = dashboard_mod
spec.loader.exec_module(dashboard_mod)

bp = getattr(dashboard_mod, 'bp')

print('\nModule symbols:')
print([name for name in dir(dashboard_mod) if not name.startswith('_')])
print('\nHas admin_login? ->', hasattr(dashboard_mod, 'admin_login'))
print('\nModule file:', getattr(dashboard_mod, '__file__', None))

# Also dump the raw file contents (search for 'def admin_login')
with open(bp_path, 'r', encoding='utf-8') as f:
    txt = f.read()
print('\nFile contains def admin_login?:', 'def admin_login' in txt)
print('\nSnippet around def admin_login:')
idx = txt.find('def admin_login')
if idx != -1:
    print(txt[max(0, idx-120):idx+240])
else:
    print('not found')


app = Flask(__name__)
app.register_blueprint(bp, url_prefix='/dashboard')

print('\nRoutes from dashboard blueprint:')
for rule in sorted(app.url_map.iter_rules(), key=lambda r: (r.rule, r.endpoint)):
    methods = ','.join(sorted(rule.methods))
    print(f"{rule.rule:30} -> {rule.endpoint:30} [{methods}]")
