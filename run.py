"""
Pi Fleet Emulator - run without Docker for the spawner itself
Run: python run.py   (Docker is still required for the Pi nodes)
"""
import os, sys, subprocess, platform

ROOT   = os.path.dirname(os.path.abspath(__file__))
VENV   = os.path.join(ROOT, 'venv')
IS_WIN = platform.system() == 'Windows'
PYTHON = os.path.join(VENV, 'Scripts', 'python.exe') if IS_WIN else os.path.join(VENV, 'bin', 'python')

def ok(m):  print(f'  \033[92m✔\033[0m  {m}')
def run(c): subprocess.run(c, check=True)

def ensure_venv():
    if os.path.isfile(PYTHON): ok('venv ready'); return
    print('  Creating virtual environment…')
    run([sys.executable, '-m', 'venv', VENV])
    ok('venv created')

def reexec():
    if os.path.realpath(sys.executable) == os.path.realpath(PYTHON): return
    print('  Switching to venv…')
    if IS_WIN:  # os.execv on Windows detaches from the console; use a child process
        sys.exit(subprocess.call([PYTHON] + sys.argv))
    os.execv(PYTHON, [PYTHON] + sys.argv)

def ensure_deps():
    probe = subprocess.run([PYTHON, '-c', 'import flask'], capture_output=True)
    if probe.returncode == 0: ok('dependencies ready'); return
    print('  Installing dependencies…')
    run([PYTHON, '-m', 'pip', 'install', '-r', os.path.join(ROOT, 'requirements.txt'), '--quiet'])
    ok('dependencies installed')

def ensure_docker():
    try:
        r = subprocess.run(['docker', 'info'], capture_output=True, timeout=15)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        r = None
    if r is None or r.returncode != 0:
        print('  \033[93m!\033[0m  Docker is not running - start Docker Desktop / Engine before spawning')
    else:
        ok('docker reachable')

if __name__ == '__main__':
    print('\n  \033[1mPi Fleet Emulator\033[0m')
    print('  ' + '─' * 36)
    ensure_venv()
    reexec()
    ensure_deps()
    ensure_docker()
    print(f'\n  \033[92mOpen: http://localhost:7070\033[0m')
    print('  Ctrl+C to stop\n')
    sys.path.insert(0, os.path.join(ROOT, 'spawner'))
    from app import app
    app.run(host='127.0.0.1', port=7070, debug=False)
