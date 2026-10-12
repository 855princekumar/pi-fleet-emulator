"""Shared fixtures: import the spawner against a temp data dir, never touch real Docker."""
import importlib, json, os, subprocess, sys, tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'spawner'))

# Module-level config is read at import time, so point it somewhere harmless first
os.environ['PFE_DATA_DIR'] = tempfile.mkdtemp(prefix='pfe-test-')
os.environ.pop('PFE_NODE_IMAGE', None)

import app as app_module  # noqa: E402


class FakeDocker:
    """Records every subprocess.run call and answers like the docker CLI would."""

    def __init__(self):
        self.calls = []
        self.ps = []            # containers returned by `docker ps`
        self.returncode = 0
        self.stderr = ''

    def __call__(self, cmd, *args, **kwargs):
        self.calls.append(cmd)
        out = ''
        if cmd[:2] == ['docker', 'ps']:
            out = '\n'.join(json.dumps(c) for c in self.ps)
        elif cmd[:2] == ['docker', 'version']:
            out = '29.0.0'
        return subprocess.CompletedProcess(cmd, self.returncode, stdout=out, stderr=self.stderr)

    def ran(self, *words):
        return any(all(w in c for w in words) for c in self.calls)


@pytest.fixture
def spawner(monkeypatch, tmp_path):
    """The app module with a fresh data dir and a fake docker."""
    monkeypatch.setattr(app_module, 'DATA_DIR', str(tmp_path))
    monkeypatch.setattr(app_module, 'COMPOSE_FILE', str(tmp_path / 'docker-compose.generated.yml'))
    monkeypatch.setattr(app_module, 'CONFIG_FILE', str(tmp_path / 'fleet-config.json'))
    fake = FakeDocker()
    monkeypatch.setattr(app_module.subprocess, 'run', fake)
    app_module.docker_fake = fake
    return app_module


@pytest.fixture
def client(spawner):
    spawner.app.config['TESTING'] = True
    with spawner.app.test_client() as c:
        yield c


def post_json(client, path, body=None, **headers):
    return client.post(path, data=json.dumps(body or {}), content_type='application/json',
                       headers=headers)


@pytest.fixture
def reload_app(monkeypatch):
    """Re-import the app with different environment variables."""
    def _reload(**env):
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        return importlib.reload(app_module)
    yield _reload
    for k in ('PFE_BIND_ADDR', 'PFE_NODE_PASSWORD', 'PFE_PROJECT', 'PFE_ALLOWED_HOSTS'):
        monkeypatch.delenv(k, raising=False)
    importlib.reload(app_module)
