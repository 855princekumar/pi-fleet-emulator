"""Fleet validation, export and the pfe CLI, with docker exec mocked."""
import argparse, json, os, sys

import pytest

from conftest import ROOT, post_json

NODES = [{'name': 'node-1', 'arch': 'aarch64', 'debian': 'bookworm'},
         {'name': 'node-2', 'arch': 'armv7l', 'debian': 'bullseye'}]
HEALTHY = {'pi-emu-node-1': 'aarch64\nbookworm\nSSH-2.0\n200\nyes\n',
           'pi-emu-node-2': 'armv7l\nbullseye\nSSH-2.0\n200\nyes\n'}


@pytest.fixture
def fleet(spawner, monkeypatch):
    spawner.save_config({'nodes': NODES, 'network': '10.20.0'})
    spawner.docker_fake.ps = [{'Names': n, 'Status': 'Up', 'Ports': f'127.0.0.1:{3000 + i}->22/tcp'}
                              for i, n in enumerate(HEALTHY)]
    outputs = dict(HEALTHY)
    mqtt = {'got': 'ok'}

    def fake_exec(container, script, timeout=20):
        if script.startswith('cat /tmp/pfe-mq.out'):
            return 0, mqtt['got']
        if 'uname -m' in script:
            return 0, outputs[container]
        return 0, ''
    monkeypatch.setattr(spawner, '_exec', fake_exec)
    monkeypatch.setattr(spawner.time, 'sleep', lambda s: None)
    spawner.fleet_outputs, spawner.fleet_mqtt = outputs, mqtt
    return spawner


def test_healthy_fleet_passes(fleet):
    r = fleet.validate_fleet()
    assert r['ok'] and r['running'] == 2 and r['mqtt']['ok']
    assert all(all(n['checks'].values()) for n in r['nodes'])


@pytest.mark.parametrize('broken_line, check', [(0, 'arch'), (1, 'os'), (2, 'ssh'), (3, 'node_red'), (4, 'metrics')])
def test_each_failed_check_is_reported(fleet, broken_line, check):
    lines = fleet.fleet_outputs['pi-emu-node-1'].splitlines()
    lines[broken_line] = 'nope'
    fleet.fleet_outputs['pi-emu-node-1'] = '\n'.join(lines)
    r = fleet.validate_fleet()
    assert not r['ok']
    assert r['nodes'][0]['checks'][check] is False
    assert all(r['nodes'][1]['checks'].values())


def test_mqtt_failure_fails_fleet(fleet):
    fleet.fleet_mqtt['got'] = ''
    assert not fleet.validate_fleet()['ok']


def test_missing_node_fails_fleet(fleet):
    fleet.docker_fake.ps = fleet.docker_fake.ps[:1]
    r = fleet.validate_fleet()
    assert not r['ok'] and r['nodes'][1]['checks'] == {'running': False} and r['mqtt'] is None


def test_validate_endpoint_status_codes(client, fleet):
    assert client.get('/api/validate').status_code == 200
    fleet.fleet_mqtt['got'] = ''
    assert client.get('/api/validate').status_code == 503


def test_export_uses_saved_arch(client, fleet):
    d = json.loads(client.get('/api/export-edgeshell').data)
    tags = {n['name']: n['tags'] for n in d['nodes']}
    assert d['node_count'] == 2
    assert tags == {'Node 1': 'simulated,64bit', 'Node 2': 'simulated,32bit'}
    assert {n['ssh_port'] for n in d['nodes']} == {3000, 3001}


# ── pfe CLI ────────────────────────────────────────────────────────

sys.path.insert(0, os.path.join(ROOT, 'spawner'))
import pfe  # noqa: E402


def test_pick_arch():
    assert [pfe.pick_arch('mixed', i) for i in range(4)] == ['aarch64', 'armv7l', 'aarch64', 'armv7l']
    assert pfe.pick_arch('armv7l', 3) == 'armv7l'


@pytest.fixture
def cli(monkeypatch):
    sent = {}
    saved = {'nodes': [{'name': 'node-1', 'arch': 'aarch64', 'debian': 'bookworm'},
                       {'name': 'node-3', 'arch': 'armv7l', 'debian': 'bookworm'}]}

    def fake_call(method, path, body=None, timeout=0):
        if path == '/api/saved-config':
            return 200, {'found': True, 'config': json.loads(json.dumps(saved))}
        sent[path] = body
        return 200, {'success': True, 'node_count': len((body or {}).get('nodes', []))}
    monkeypatch.setattr(pfe, 'call', fake_call)
    return sent


def scale(n, arch='mixed'):
    pfe.cmd_scale(argparse.Namespace(count=n, arch=arch, debian='bookworm', validate=False, wait=0))


def test_scale_up_keeps_existing_and_fills_gaps(cli):
    scale(4)
    names = [n['name'] for n in cli['/api/spawn']['nodes']]
    assert names == ['node-1', 'node-3', 'node-2', 'node-4']


def test_scale_down_drops_newest(cli):
    scale(1)
    assert [n['name'] for n in cli['/api/spawn']['nodes']] == ['node-1']


def test_scale_to_zero_is_refused(cli):
    with pytest.raises(SystemExit):
        scale(0)


def test_spawn_builds_mixed_fleet(cli):
    pfe.cmd_spawn(argparse.Namespace(count=3, arch='mixed', debian='bullseye', subnet='10.30.0',
                                     ssh_port=5000, nr_port=6000, validate=False, wait=0))
    body = cli['/api/spawn']
    assert [n['arch'] for n in body['nodes']] == ['aarch64', 'armv7l', 'aarch64']
    assert body['network'] == '10.30.0' and body['base_ssh_port'] == 5000


def test_reset_needs_yes(cli):
    with pytest.raises(SystemExit):
        pfe.cmd_reset(argparse.Namespace(yes=False))
    assert '/api/clear-config' not in cli
    pfe.cmd_reset(argparse.Namespace(yes=True))
    assert '/api/clear-config' in cli
