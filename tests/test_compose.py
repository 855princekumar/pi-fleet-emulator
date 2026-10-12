"""The generated compose file: networking, binding, secrets, persistence, image modes."""
import json, re, shutil, subprocess

import pytest
import yaml

real_run = subprocess.run   # captured before the spawner fixture swaps in the fake

from conftest import post_json

NODES = [{'name': 'node-1', 'arch': 'aarch64', 'debian': 'bookworm'},
         {'name': 'node-2', 'arch': 'armv7l', 'debian': 'bullseye'}]


def build(spawner, **kw):
    return yaml.safe_load(spawner._build_compose(NODES, '10.20.0', 3000, 4000, kw.get('es', '')))


def test_services_ports_and_ips(spawner):
    doc = build(spawner)
    a, b = doc['services']['pi-emu-node-1'], doc['services']['pi-emu-node-2']
    assert a['ports'] == ['127.0.0.1:3000:22', '127.0.0.1:4000:1880']
    assert b['ports'] == ['127.0.0.1:3001:22', '127.0.0.1:4001:1880']
    assert a['networks']['pi_fleet_net']['ipv4_address'] == '10.20.0.20'
    assert b['networks']['pi_fleet_net']['ipv4_address'] == '10.20.0.21'
    assert doc['networks']['pi_fleet_net']['ipam']['config'][0]['subnet'] == '10.20.0.0/24'


def test_simulation_environment(spawner):
    env = build(spawner)['services']['pi-emu-node-2']['environment']
    assert env['SIM_ARCH'] == 'armv7l'
    assert env['SIM_DEBIAN'] == 'bullseye'
    assert env['SIM_OS'] == 'Raspberry Pi OS 32-bit bullseye'


def test_no_extra_privileges(spawner):
    for svc in build(spawner)['services'].values():
        assert 'cap_add' not in svc and 'privileged' not in svc
        assert not any('docker.sock' in v for v in svc.get('volumes', []))


def test_persistent_home_volumes(spawner):
    doc = build(spawner)
    assert doc['services']['pi-emu-node-1']['volumes'] == ['pi-emu-node-1-home:/home/pi']
    assert set(doc['volumes']) == {'pi-emu-node-1-home', 'pi-emu-node-2-home'}


def test_persistence_can_be_disabled(spawner, monkeypatch):
    monkeypatch.setattr(spawner, 'PERSIST_HOME', False)
    doc = build(spawner)
    assert 'volumes' not in doc and 'volumes' not in doc['services']['pi-emu-node-1']


def test_bind_address_lan_and_ipv6(spawner, monkeypatch):
    monkeypatch.setattr(spawner, 'BIND_ADDR', '0.0.0.0')
    assert build(spawner)['services']['pi-emu-node-1']['ports'][0] == '0.0.0.0:3000:22'
    monkeypatch.setattr(spawner, 'BIND_ADDR', '::1')
    assert build(spawner)['services']['pi-emu-node-1']['ports'][0] == '[::1]:3000:22'


def test_password_is_escaped_for_yaml_and_compose(spawner, monkeypatch):
    nasty = 'p@ss"w:rd $HOME \\ #x'
    monkeypatch.setattr(spawner, 'NODE_PASSWORD', nasty)
    text = spawner._build_compose(NODES, '10.20.0', 3000, 4000)
    env = yaml.safe_load(text)['services']['pi-emu-node-1']['environment']
    # compose turns $$ back into $, so the node receives the password unchanged
    assert env['NODE_PASSWORD'].replace('$$', '$') == nasty
    # no lone $ left for compose to interpolate
    assert not re.search(r'(?<!\$)\$(?!\$)', text.replace('$$', ''))


@pytest.mark.skipif(not shutil.which('docker'), reason='docker CLI not installed')
def test_compose_delivers_exact_password(spawner, monkeypatch, tmp_path):
    nasty = 'p@ss"w:rd $HOME ${X} \\ #x'
    monkeypatch.setattr(spawner, 'NODE_PASSWORD', nasty)
    f = tmp_path / 'c.yml'
    f.write_text(spawner._build_compose(NODES, '10.20.0', 3000, 4000), encoding='utf-8')
    out = real_run(['docker', 'compose', '-f', str(f), 'config', '--format', 'json'],
                   capture_output=True, text=True)
    if out.returncode != 0:
        pytest.skip('docker compose unavailable: ' + out.stderr[:80])
    env = json.loads(out.stdout)['services']['pi-emu-node-1']['environment']
    # `config` prints a compose file, so it re-escapes $ as $$ in its own output;
    # the container itself receives the exact password (verified with a real run)
    assert env['NODE_PASSWORD'].replace('$$', '$') == nasty


def test_build_mode_vs_prebuilt_image(spawner, monkeypatch):
    svc = build(spawner)['services']['pi-emu-node-1']
    assert svc['image'] == 'pi-fleet-node:local' and 'build' in svc
    monkeypatch.setattr(spawner, 'NODE_IMAGE', 'devprincekumar/pi-fleet-node:1.1.0')
    svc = build(spawner)['services']['pi-emu-node-1']
    assert svc['image'] == 'devprincekumar/pi-fleet-node:1.1.0' and 'build' not in svc


def test_external_edgeshell_network(spawner):
    doc = build(spawner, es='edgenet')
    assert doc['networks']['edgenet'] == {'external': True}
    assert 'edgenet' in doc['services']['pi-emu-node-1']['networks']


def test_spawn_writes_config_and_runs_compose(client, spawner):
    r = post_json(client, '/api/spawn', {'nodes': NODES})
    assert r.status_code == 200 and r.get_json()['node_count'] == 2
    assert spawner.docker_fake.ran('compose', '-p', spawner.PROJECT, 'up', '--remove-orphans')
    assert spawner.load_config()['nodes'][1]['arch'] == 'armv7l'


def test_spawn_reports_compose_failure(client, spawner):
    spawner.docker_fake.returncode, spawner.docker_fake.stderr = 1, 'port is already allocated'
    r = post_json(client, '/api/spawn', {'nodes': NODES})
    assert r.status_code == 500 and 'already allocated' in r.get_json()['error']


def test_spawn_is_refused_while_another_runs(client, spawner):
    assert spawner.FLEET_LOCK.acquire(blocking=False)
    try:
        assert post_json(client, '/api/spawn', {'nodes': NODES}).status_code == 409
    finally:
        spawner.FLEET_LOCK.release()


def test_reset_removes_project_volumes(client, spawner):
    post_json(client, '/api/spawn', {'nodes': NODES})
    assert post_json(client, '/api/clear-config').status_code == 200
    assert spawner.docker_fake.ran('compose', 'down', '-v')
    assert spawner.docker_fake.ran('volume', 'ls', f'label=com.docker.compose.project={spawner.PROJECT}')
    assert spawner.load_config() is None


def test_status_only_lists_this_project(client, spawner):
    client.get('/api/status')
    assert spawner.docker_fake.ran('ps', f'label=com.docker.compose.project={spawner.PROJECT}')
