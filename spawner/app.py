"""
Pi Fleet Emulator - Spawner
Flask GUI + API that configures and launches simulated Raspberry Pi nodes.

Runs either inside Docker (docker compose up - talks to the host engine via the
mounted socket) or directly on the host (python run.py).
"""
import subprocess, json, os, re, time
from flask import Flask, render_template, request, jsonify, Response

app = Flask(__name__)

ROOT_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR     = os.environ.get('PFE_DATA_DIR', ROOT_DIR)
NODE_BASE    = os.environ.get('PFE_NODE_BASE', os.path.join(ROOT_DIR, 'node-base'))
COMPOSE_FILE = os.path.join(DATA_DIR, 'docker-compose.generated.yml')
CONFIG_FILE  = os.path.join(DATA_DIR, 'fleet-config.json')
PROJECT      = 'pi-fleet'   # fixed compose project name, wherever the file lives
MAX_NODES    = 20

os.makedirs(DATA_DIR, exist_ok=True)

DEBIAN_VERSIONS = [
    {'id': 'bookworm', 'label': 'Debian 12 Bookworm (latest, recommended)'},
    {'id': 'bullseye', 'label': 'Debian 11 Bullseye (stable)'},
    {'id': 'buster',   'label': 'Debian 10 Buster (legacy)'},
]
ARCH_OPTIONS = [
    {'id': 'aarch64', 'label': 'ARM64 / aarch64 - 64-bit (Pi 4, Pi 5)'},
    {'id': 'armv7l',  'label': 'ARMv7 / armhf - 32-bit (Pi 2, Pi 3)'},
]
VALID_DEBIAN = {d['id'] for d in DEBIAN_VERSIONS}
VALID_ARCH   = {a['id'] for a in ARCH_OPTIONS}

def compose_cmd(*args):
    return ['docker', 'compose', '-p', PROJECT, '-f', COMPOSE_FILE, *args]

def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f: json.dump(cfg, f, indent=2)

def load_config():
    if not os.path.isfile(CONFIG_FILE): return None
    try:
        with open(CONFIG_FILE) as f: return json.load(f)
    except Exception: return None

def clear_config():
    for p in [CONFIG_FILE, COMPOSE_FILE]:
        if os.path.isfile(p): os.remove(p)

def service_name(name):
    """Turn a user-supplied node name into a safe container/service name."""
    slug = re.sub(r'[^a-z0-9-]+', '-', str(name).lower()).strip('-')[:40]
    return f'pi-emu-{slug or "node"}'

def docker_ps():
    try:
        r = subprocess.run(['docker','ps','--format','{{json .}}'],
                           capture_output=True, text=True, timeout=8)
        result = []
        for line in r.stdout.strip().splitlines():
            if not line.strip(): continue
            try:
                c = json.loads(line)
                if 'pi-emu-' in c.get('Names',''):
                    result.append(c)
            except Exception: pass
        return result
    except Exception: return []

def parse_port(ports_str, internal):
    for part in ports_str.split(','):
        part = part.strip()
        if f'->{internal}/tcp' in part:
            try: return int(part.split('->')[0].rsplit(':', 1)[1])
            except Exception: pass
    return None

def docker_networks():
    try:
        r = subprocess.run(['docker','network','ls','--format','{{json .}}'],
                           capture_output=True, text=True, timeout=5)
        nets = []
        for line in r.stdout.strip().splitlines():
            if not line.strip(): continue
            try:
                n = json.loads(line)
                name = n.get('Name','')
                if 'edge' in name.lower() and name not in ('bridge','host','none'):
                    nets.append({'id': name, 'label': name})
            except Exception: pass
        return nets
    except Exception: return []

def validate(cfg):
    """Return (clean_config, error). Everything here ends up in generated YAML."""
    nodes = cfg.get('nodes') or []
    if not nodes: return None, 'No nodes configured'
    if len(nodes) > MAX_NODES: return None, f'Maximum {MAX_NODES} nodes'

    clean_nodes, seen = [], set()
    for n in nodes:
        sname = service_name(n.get('name', 'node'))
        if sname in seen: return None, f'Duplicate node name: {sname}'
        seen.add(sname)
        arch   = n.get('arch', 'aarch64')
        debian = n.get('debian', 'bookworm')
        if arch not in VALID_ARCH:     return None, f'Unknown architecture: {arch}'
        if debian not in VALID_DEBIAN: return None, f'Unknown Debian version: {debian}'
        clean_nodes.append({'name': sname[len('pi-emu-'):], 'arch': arch, 'debian': debian})

    network = str(cfg.get('network', '10.20.0')).strip()
    octets  = network.split('.')[:3]
    if len(octets) != 3 or not all(o.isdigit() and 0 <= int(o) <= 255 for o in octets):
        return None, 'Fleet subnet must look like 10.20.0'

    try:
        base_ssh = int(cfg.get('base_ssh_port', 3000))
        base_nr  = int(cfg.get('base_nr_port',  4000))
    except (TypeError, ValueError):
        return None, 'Ports must be numbers'
    for p in (base_ssh, base_nr):
        if not 1024 <= p <= 65535 - MAX_NODES:
            return None, 'Base ports must be between 1024 and 65515'
    ssh_range = set(range(base_ssh, base_ssh + len(clean_nodes)))
    nr_range  = set(range(base_nr,  base_nr  + len(clean_nodes)))
    if ssh_range & nr_range: return None, 'SSH and Node-RED port ranges overlap'

    es_net = str(cfg.get('edgeshell_network', '') or '')
    if es_net and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', es_net):
        return None, 'Invalid EdgeShell network name'

    return {'nodes': clean_nodes, 'network': '.'.join(octets),
            'base_ssh_port': base_ssh, 'base_nr_port': base_nr,
            'edgeshell_network': es_net}, None

@app.route('/')
def index():
    return render_template('index.html',
        debian_versions=DEBIAN_VERSIONS, arch_options=ARCH_OPTIONS,
        running=docker_ps(), saved_cfg=load_config())

@app.route('/api/saved-config')
def saved_config_route():
    cfg = load_config()
    return jsonify({'found': cfg is not None, 'config': cfg})

@app.route('/api/spawn', methods=['POST'])
def spawn():
    cfg, err = validate(request.get_json(silent=True) or {})
    if err: return jsonify({'error': err}), 400

    save_config(cfg)
    compose = _build_compose(cfg['nodes'], cfg['network'], cfg['base_ssh_port'],
                             cfg['base_nr_port'], cfg['edgeshell_network'])
    with open(COMPOSE_FILE, 'w') as f: f.write(compose)

    try:
        r = subprocess.run(compose_cmd('up', '--build', '-d', '--remove-orphans'),
                           capture_output=True, text=True, timeout=600, cwd=DATA_DIR)
        if r.returncode != 0:
            return jsonify({'error': r.stderr[-3000:] or r.stdout[-1000:]}), 500
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Build timed out (>10 min)'}), 500
    except FileNotFoundError:
        return jsonify({'error': 'docker not found - is Docker running (and the socket mounted)?'}), 500

    return jsonify({'success': True, 'node_count': len(cfg['nodes'])})

@app.route('/api/stop', methods=['POST'])
def stop():
    data = request.get_json(silent=True) or {}
    keep = data.get('keep_config', True)
    if os.path.isfile(COMPOSE_FILE):
        subprocess.run(compose_cmd('down'), capture_output=True, timeout=120, cwd=DATA_DIR)
    if not keep: clear_config()
    return jsonify({'success': True, 'config_kept': keep})

@app.route('/api/clear-config', methods=['POST'])
def clear_config_route():
    if os.path.isfile(COMPOSE_FILE):
        subprocess.run(compose_cmd('down'), capture_output=True, timeout=120, cwd=DATA_DIR)
    clear_config()
    return jsonify({'success': True})

@app.route('/api/status')
def status():
    containers = docker_ps()
    nodes = []
    for c in containers:
        ports = c.get('Ports','')
        nodes.append({'name': c['Names'], 'status': c['Status'],
                      'ports': ports,
                      'ssh_port': parse_port(ports,'22'),
                      'nr_port':  parse_port(ports,'1880')})
    cfg = load_config()
    return jsonify({'nodes': nodes, 'count': len(nodes), 'has_config': cfg is not None})

@app.route('/api/logs/<container>')
def logs(container):
    if not re.fullmatch(r'pi-emu-[a-z0-9-]+', container):
        return jsonify({'error': 'Invalid container'}), 400
    try:
        r = subprocess.run(['docker','logs','--tail','120',container],
                           capture_output=True, text=True, timeout=10)
        return jsonify({'logs': r.stdout + r.stderr})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/detect-edgeshell-networks')
def detect_networks():
    return jsonify({'networks': docker_networks()})

@app.route('/api/export-edgeshell')
def export_edgeshell():
    containers = docker_ps()
    cfg        = load_config() or {}
    es_net     = cfg.get('edgeshell_network','')
    arch_by_name = {service_name(n.get('name')): n.get('arch') for n in cfg.get('nodes', [])}
    nodes_out  = []
    for c in containers:
        name     = c['Names']
        ports    = c.get('Ports','')
        ssh_port = parse_port(ports,'22')
        arch_tag = '64bit' if arch_by_name.get(name, 'aarch64') == 'aarch64' else '32bit'
        if es_net:
            ip, port = name, 22
        else:
            ip, port = 'host.docker.internal', (ssh_port or 22)
        nodes_out.append({
            'name':        name.replace('pi-emu-','').replace('-',' ').title(),
            'ip_address':  ip,
            'ssh_port':    port,
            'username':    'pi',
            'description': f'Pi Fleet Emulator ({name}) - {arch_tag}',
            'tags':        f'simulated,{arch_tag}',
        })
    payload = {
        'edgeshell_export': True, 'version': '1.0',
        'exported_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'node_count':  len(nodes_out), 'nodes': nodes_out,
    }
    return Response(json.dumps(payload, indent=2), mimetype='application/json',
        headers={'Content-Disposition': 'attachment; filename=pi-fleet-nodes.json'})

def _build_compose(nodes, network, base_ssh, base_nr, es_network=''):
    net    = 'pi_fleet_net'
    prefix = network
    lines  = ['networks:',
              f'  {net}:','    driver: bridge','    ipam:','      config:',
              f'        - subnet: {prefix}.0/24',
              f'          gateway: {prefix}.1']
    if es_network:
        lines += [f'  {es_network}:','    external: true']
    lines += ['','services:']
    context = NODE_BASE.replace('\\', '/')
    for i, node in enumerate(nodes):
        sname  = service_name(node['name'])
        arch   = node['arch']
        debian = node['debian']
        bits   = '64-bit' if arch == 'aarch64' else '32-bit'
        os_str = f'Raspberry Pi OS {bits} {debian}'
        ssh_p  = base_ssh + i
        nr_p   = base_nr  + i
        ip     = f'{prefix}.{20+i}'
        lines += [
            f'  {sname}:',
            f'    build:',
            f'      context: "{context}"',
            f'      args:',
            f'        NODE_NAME: "{sname}"',
            f'        NODE_USER: "pi"',
            f'        NODE_PASSWORD: "raspberry"',
            f'        NODE_ARCH: "{arch}"',
            f'        NODE_OS: "{os_str}"',
            f'    container_name: {sname}',
            f'    hostname: {sname}',
            f'    restart: unless-stopped',
            f'    environment:',
            f'      NODE_NAME: "{sname}"',
            f'      NODE_USER: "pi"',
            f'      SIM_ARCH: "{arch}"',
            f'      SIM_OS: "{os_str}"',
            f'      SIM_DEBIAN: "{debian}"',
            f'    ports:',
            f'      - "{ssh_p}:22"',
            f'      - "{nr_p}:1880"',
            f'    networks:',
            f'      {net}:',
            f'        ipv4_address: {ip}',
        ]
        if es_network: lines.append(f'      {es_network}: {{}}')
        lines += ['    cap_add:','      - SYS_PTRACE']
    return '\n'.join(lines)+'\n'

if __name__ == '__main__':
    print('\n  Pi Fleet Emulator - Spawner')
    print('  Open: http://localhost:7070\n')
    app.run(host='127.0.0.1', port=7070, debug=False)
