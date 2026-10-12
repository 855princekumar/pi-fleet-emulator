"""Request guard: DNS rebinding, CSRF, content type, response headers, env validation."""
import pytest

from conftest import app_module as app, post_json


@pytest.mark.parametrize('hostport, host', [
    ('localhost:7070', 'localhost'),
    ('127.0.0.1:7070', '127.0.0.1'),
    ('[::1]:7070', '::1'),
    ('localhost', 'localhost'),
    ('LOCALHOST:7070', 'localhost'),
    ('attacker.example:7070', 'attacker.example'),
])
def test_host_only(hostport, host):
    assert app._host_only(hostport) == host


@pytest.mark.parametrize('host', ['attacker.example', 'attacker.example:7070',
                                  'localhost.attacker.example', '127.0.0.1.nip.io'])
def test_dns_rebinding_hosts_are_refused(client, host):
    assert client.get('/api/saved-config', headers={'Host': host}).status_code == 403


@pytest.mark.parametrize('host', ['localhost:7070', '127.0.0.1:7070', '[::1]:7070'])
def test_local_hosts_are_allowed(client, host):
    assert client.get('/api/saved-config', headers={'Host': host}).status_code == 200


def test_cross_origin_post_is_refused_and_nothing_runs(client, spawner):
    r = post_json(client, '/api/clear-config', Origin='http://evil.example')
    assert r.status_code == 403
    assert not spawner.docker_fake.calls


def test_null_origin_is_refused(client):
    assert post_json(client, '/api/stop', Origin='null').status_code == 403


@pytest.mark.parametrize('ctype', ['text/plain', 'application/x-www-form-urlencoded', 'multipart/form-data'])
def test_simple_form_posts_are_refused(client, spawner, ctype):
    r = client.post('/api/clear-config', data='a=b', content_type=ctype)
    assert r.status_code == 415
    assert not spawner.docker_fake.calls


def test_same_origin_json_post_is_allowed(client):
    r = post_json(client, '/api/stop', {'keep_config': True}, Origin='http://localhost')
    assert r.status_code == 200


def test_security_headers(client):
    h = client.get('/api/saved-config').headers
    assert h['X-Frame-Options'] == 'DENY'
    assert h['X-Content-Type-Options'] == 'nosniff'
    assert h['Referrer-Policy'] == 'no-referrer'
    csp = h['Content-Security-Policy']
    for directive in ("default-src 'self'", "frame-ancestors 'none'", "connect-src 'self'"):
        assert directive in csp


@pytest.mark.parametrize('container', ['pi-fleet-spawner', '../etc', 'pi-emu-a;id', 'pi-emu-A'])
def test_logs_only_for_node_containers(client, container):
    assert client.get(f'/api/logs/{container}').status_code in (400, 404)


def test_allowed_hosts_is_configurable(reload_app):
    mod = reload_app(PFE_ALLOWED_HOSTS='fleet.lan')
    with mod.app.test_client() as c:
        assert c.get('/api/saved-config', headers={'Host': 'fleet.lan:7070'}).status_code == 200
        assert c.get('/api/saved-config', headers={'Host': 'localhost'}).status_code == 403


@pytest.mark.parametrize('env, value', [
    ('PFE_BIND_ADDR', 'not-an-ip'),
    ('PFE_BIND_ADDR', '0.0.0.0; rm'),
    ('PFE_NODE_PASSWORD', 'two\nlines'),
    ('PFE_NODE_PASSWORD', ''),
    ('PFE_PROJECT', 'Has Spaces'),
])
def test_bad_environment_stops_startup(reload_app, env, value):
    with pytest.raises(SystemExit):
        reload_app(**{env: value})
