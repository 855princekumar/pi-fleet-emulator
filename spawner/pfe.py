"""
pfe - command line for the Pi Fleet Emulator spawner.

Talks to the spawner API, so it works from inside the spawner container:
  docker exec pi-fleet-spawner pfe spawn 3
or from the host with Python (set PFE_URL if the spawner is not on localhost:7070).
"""
import argparse, json, os, sys, time, urllib.request, urllib.error

URL = os.environ.get('PFE_URL', 'http://127.0.0.1:7070').rstrip('/')
ARCHES = ('aarch64', 'armv7l')


def call(method, path, body=None, timeout=1300):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(URL + path, data=data, method=method,
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b'{}')
        except ValueError:
            return e.code, {'error': str(e)}
    except urllib.error.URLError as e:
        sys.exit(f'Cannot reach the spawner at {URL}: {e.reason}')


def pick_arch(mode, i):
    return ARCHES[i % 2] if mode == 'mixed' else mode


def spawn(cfg):
    n = len(cfg['nodes'])
    print(f'Spawning {n} node(s)... (first run pulls/builds the node image)')
    code, d = call('POST', '/api/spawn', cfg)
    if code != 200:
        sys.exit('Spawn failed:\n' + d.get('error', str(d)))
    print(f'OK: {d.get("node_count")} node(s) up')


def cmd_spawn(a):
    nodes = [{'name': f'node-{i + 1}', 'arch': pick_arch(a.arch, i), 'debian': a.debian}
             for i in range(a.count)]
    spawn({'nodes': nodes, 'network': a.subnet,
           'base_ssh_port': a.ssh_port, 'base_nr_port': a.nr_port})
    if a.validate:
        cmd_validate(argparse.Namespace(wait=a.wait, json=False))


def cmd_scale(a):
    code, d = call('GET', '/api/saved-config')
    cfg = d.get('config') or {}
    nodes = list(cfg.get('nodes', []))
    if not nodes:
        sys.exit('No saved fleet. Use "pfe spawn N" first.')
    if a.count < 1:
        sys.exit('Count must be at least 1 (use "pfe stop" to stop everything).')
    used = {n['name'] for n in nodes}
    k = 1
    while len(nodes) < a.count:
        while f'node-{k}' in used: k += 1
        nodes.append({'name': f'node-{k}', 'arch': pick_arch(a.arch, len(nodes)), 'debian': a.debian})
        used.add(f'node-{k}')
    del nodes[a.count:]
    cfg['nodes'] = nodes
    spawn(cfg)
    if a.validate:
        cmd_validate(argparse.Namespace(wait=a.wait, json=False))


def cmd_status(a):
    _, d = call('GET', '/api/status')
    if a.json: return print(json.dumps(d, indent=2))
    if not d.get('nodes'): return print('No nodes running.')
    print(f'{"NODE":<24}{"SSH":>7}{"NODE-RED":>10}  STATUS')
    for n in sorted(d['nodes'], key=lambda n: n.get('ssh_port') or 0):
        print(f'{n["name"]:<24}{n.get("ssh_port") or "-":>7}{n.get("nr_port") or "-":>10}  {n["status"]}')
    print('\nssh pi@localhost -p <SSH>   (password: raspberry)')


def cmd_validate(a):
    deadline = time.time() + a.wait
    while True:
        code, d = call('GET', '/api/validate', timeout=180)
        if d.get('ok') or time.time() >= deadline: break
        time.sleep(5)   # services (Node-RED especially) need a few seconds after start
    if getattr(a, 'json', False):
        print(json.dumps(d, indent=2))
    else:
        if not d.get('expected'):
            sys.exit('No saved fleet to validate. Use "pfe spawn N" first.')
        cols = ('running', 'arch', 'os', 'ssh', 'node_red', 'metrics')
        print(f'{"NODE":<22}{"ARCH":<9}' + ''.join(f'{c.upper():<10}' for c in cols))
        for n in d['nodes']:
            marks = ''.join(f'{("PASS" if n["checks"].get(c) else "FAIL"):<10}' for c in cols)
            print(f'{n["name"]:<22}{n["arch"]:<9}{marks}')
        if d.get('mqtt'):
            m = d['mqtt']
            print(f'\nMQTT {m["from"]} -> {m["to"]}: {"PASS" if m["ok"] else "FAIL"}')
        print(f'\n{d["running"]}/{d["expected"]} nodes running. Fleet: {"PASS" if d["ok"] else "FAIL"}')
    sys.exit(0 if d.get('ok') else 1)


def cmd_health(a):
    code, d = call('GET', '/api/health')
    print(json.dumps(d, indent=2))
    sys.exit(0 if code == 200 else 1)


def cmd_stop(a):
    call('POST', '/api/stop', {'keep_config': True})
    print('Fleet stopped. Config and node data kept. "pfe scale N" or the GUI brings it back.')


def cmd_reset(a):
    if not a.yes:
        sys.exit('This deletes the saved fleet AND every node\'s /home/pi data. Re-run with --yes.')
    call('POST', '/api/clear-config')
    print('Fleet removed, config and node volumes deleted.')


def cmd_export(a):
    req = urllib.request.Request(URL + '/api/export-edgeshell')
    with urllib.request.urlopen(req, timeout=30) as r:
        sys.stdout.write(r.read().decode())


def main():
    p = argparse.ArgumentParser(prog='pfe', description='Pi Fleet Emulator command line')
    sub = p.add_subparsers(dest='cmd', required=True)

    def fleet_opts(sp):
        sp.add_argument('--arch', choices=['aarch64', 'armv7l', 'mixed'], default='mixed',
                        help='architecture for new nodes (default: mixed, alternating)')
        sp.add_argument('--debian', choices=['bookworm', 'bullseye', 'buster'], default='bookworm')
        sp.add_argument('--validate', action='store_true', help='run validate afterwards')
        sp.add_argument('--wait', type=int, default=120, help='seconds validate may wait for services')

    s = sub.add_parser('spawn', help='spawn a fresh fleet of N nodes (replaces the current one)')
    s.add_argument('count', type=int)
    s.add_argument('--subnet', default='10.20.0')
    s.add_argument('--ssh-port', type=int, default=3000)
    s.add_argument('--nr-port', type=int, default=4000)
    fleet_opts(s); s.set_defaults(fn=cmd_spawn)

    s = sub.add_parser('scale', help='grow or shrink the saved fleet to N nodes, keeping existing ones')
    s.add_argument('count', type=int)
    fleet_opts(s); s.set_defaults(fn=cmd_scale)

    s = sub.add_parser('status', help='list running nodes and their ports')
    s.add_argument('--json', action='store_true'); s.set_defaults(fn=cmd_status)

    s = sub.add_parser('validate', help='check arch, OS, SSH, Node-RED, metrics and MQTT on every node')
    s.add_argument('--wait', type=int, default=120)
    s.add_argument('--json', action='store_true'); s.set_defaults(fn=cmd_validate)

    sub.add_parser('health', help='check the spawner can reach Docker').set_defaults(fn=cmd_health)
    sub.add_parser('stop', help='stop all nodes, keep config and data').set_defaults(fn=cmd_stop)
    s = sub.add_parser('reset', help='remove nodes, saved config and node data')
    s.add_argument('--yes', action='store_true'); s.set_defaults(fn=cmd_reset)
    sub.add_parser('export', help='print the fleet as EdgeShell JSON').set_defaults(fn=cmd_export)

    a = p.parse_args()
    a.fn(a)


if __name__ == '__main__':
    main()
