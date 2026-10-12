"""Input validation: everything here ends up inside a generated compose file."""
import pytest

from conftest import app_module as app


def nodes(*names, **extra):
    return {'nodes': [{'name': n, **extra} for n in names]}


@pytest.mark.parametrize('raw, expected', [
    ('node-1', 'pi-emu-node-1'),
    ('Factory 01', 'pi-emu-factory-01'),
    ('a"; rm -rf / #', 'pi-emu-a-rm--rf'),
    ('<img src=x onerror=alert(1)>', 'pi-emu-img-src-x-onerror-alert-1'),
    ('', 'pi-emu-node'),
    ('---', 'pi-emu-node'),
    ('x' * 80, 'pi-emu-' + 'x' * 40),
])
def test_service_name_is_always_safe(raw, expected):
    assert app.service_name(raw) == expected


def test_valid_config_is_normalised():
    cfg, err = app.validate({**nodes('Node A', arch='armv7l', debian='buster'),
                             'network': ' 10.30.0 ', 'base_ssh_port': '5000', 'base_nr_port': 6000})
    assert err is None
    assert cfg['nodes'] == [{'name': 'node-a', 'arch': 'armv7l', 'debian': 'buster'}]
    assert cfg['network'] == '10.30.0'
    assert (cfg['base_ssh_port'], cfg['base_nr_port']) == (5000, 6000)


def test_defaults():
    cfg, err = app.validate(nodes('a'))
    assert err is None
    assert cfg['nodes'][0] == {'name': 'a', 'arch': 'aarch64', 'debian': 'bookworm'}
    assert (cfg['network'], cfg['base_ssh_port'], cfg['base_nr_port']) == ('10.20.0', 3000, 4000)


@pytest.mark.parametrize('cfg, message', [
    ({}, 'No nodes configured'),
    ({'nodes': []}, 'No nodes configured'),
    (nodes(*[f'n{i}' for i in range(21)]), 'Maximum 20 nodes'),
    (nodes('a', 'A'), 'Duplicate node name'),
    (nodes('a', arch='x86_64'), 'Unknown architecture'),
    (nodes('a', arch='x86\nprivileged: true'), 'Unknown architecture'),
    (nodes('a', debian='jessie'), 'Unknown Debian version'),
    ({**nodes('a'), 'network': '10.20.0; id'}, 'Fleet subnet'),
    ({**nodes('a'), 'network': '10.20'}, 'Fleet subnet'),
    ({**nodes('a'), 'network': '10.256.0'}, 'Fleet subnet'),
    ({**nodes('a'), 'base_ssh_port': 'abc'}, 'Ports must be numbers'),
    ({**nodes('a'), 'base_ssh_port': 22}, 'Base ports must be between'),
    ({**nodes('a'), 'base_nr_port': 65530}, 'Base ports must be between'),
    ({**nodes('a', 'b'), 'base_ssh_port': 5000, 'base_nr_port': 5001}, 'overlap'),
    ({**nodes('a'), 'edgeshell_network': 'x\n    privileged: true'}, 'Invalid EdgeShell network'),
    ({**nodes('a'), 'edgeshell_network': '-bad'}, 'Invalid EdgeShell network'),
])
def test_bad_input_is_rejected(cfg, message):
    result, err = app.validate(cfg)
    assert result is None
    assert message in err


def test_twenty_nodes_is_allowed():
    cfg, err = app.validate(nodes(*[f'n{i}' for i in range(20)]))
    assert err is None and len(cfg['nodes']) == 20


@pytest.mark.parametrize('ports, internal, expected', [
    ('0.0.0.0:3000->22/tcp, [::]:3000->22/tcp, 0.0.0.0:4000->1880/tcp', '22', 3000),
    ('0.0.0.0:3000->22/tcp, 0.0.0.0:4000->1880/tcp', '1880', 4000),
    ('127.0.0.1:5100->22/tcp', '22', 5100),
    (':::3001->22/tcp', '22', 3001),
    ('', '22', None),
    ('0.0.0.0:3000->22/tcp', '1880', None),
])
def test_parse_port(ports, internal, expected):
    assert app.parse_port(ports, internal) == expected
