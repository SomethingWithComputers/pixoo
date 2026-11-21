import os
import subprocess
import sys
from pathlib import Path

import pixoo

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / 'src'


def subprocess_env():
    env = os.environ.copy()
    env['PYTHONPATH'] = str(SRC) + os.pathsep + env.get('PYTHONPATH', '')
    return env


def test_all_entries_are_strings():
    assert all(isinstance(name, str) for name in pixoo.__all__)
    assert 'PixooREST' in pixoo.__all__
    assert 'TextScrollDirection' in pixoo.__all__


def test_star_import():
    namespace = {}
    exec('from pixoo import *', namespace)

    assert 'Pixoo' in namespace
    assert 'PixooREST' in namespace
    assert 'TextScrollDirection' in namespace


def test_import_without_optional_dependencies():
    code = (
        "import sys; "
        "sys.modules['tkinter'] = None; "
        "sys.modules['flask'] = None; "
        "import pixoo; "
        "print(pixoo.__version__)"
    )
    result = subprocess.run(
        [sys.executable, '-c', code],
        cwd=REPO_ROOT,
        env=subprocess_env(),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == pixoo.__version__


def test_simulator_import_without_tkinter_is_informative():
    code = (
        "import sys; "
        "sys.modules['tkinter'] = None; "
        "from pixoo import Pixoo; "
        "Pixoo(simulated=True)"
    )
    result = subprocess.run(
        [sys.executable, '-c', code],
        cwd=REPO_ROOT,
        env=subprocess_env(),
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert 'tkinter' in result.stderr


def test_rest_import_without_flask_is_informative():
    code = (
        "import sys; "
        "sys.modules['flask'] = None; "
        "from pixoo import PixooREST"
    )
    result = subprocess.run(
        [sys.executable, '-c', code],
        cwd=REPO_ROOT,
        env=subprocess_env(),
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert 'pixoo[rest]' in result.stderr
