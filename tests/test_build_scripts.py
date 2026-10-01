from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_linux_build_script_is_independent_of_the_calling_directory():
    script = (ROOT / "build_exe.sh").read_text(encoding="utf-8")

    assert 'SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"' in script
    assert 'cd "$SCRIPT_DIR"' in script
    assert 'python3 -m venv venv' in script
    assert '"$PYTHON_BIN" -m pip install -r requirements.txt' in script
    assert "--collect-all odf" in script


def test_windows_build_script_is_independent_of_the_calling_directory():
    script = (ROOT / "build_exe.bat").read_text(encoding="utf-8")

    assert 'cd /d "%~dp0"' in script
    assert "python -m pip install -r requirements.txt" in script
    assert "--collect-all odf" in script
