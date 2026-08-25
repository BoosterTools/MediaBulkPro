"""Build a single-file Windows executable with PyInstaller."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICON = ROOT / "assets" / "icons" / "mediabulk.ico"


def main() -> int:
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--windowed", "--onefile",
        "--name", "MediaBulkPro-Windows-x64",
        "--add-data", f"{ROOT / 'assets'}{';' if sys.platform.startswith('win') else ':'}assets",
        "--hidden-import", "PySide6.QtSvg",
        "--collect-submodules", "yt_dlp",
        str(ROOT / "main.py"),
    ]
    if ICON.exists():
        cmd[cmd.index("--name"):cmd.index("--name")] = ["--icon", str(ICON)]
    print(" ".join(cmd))
    return subprocess.call(cmd, cwd=ROOT)


if __name__ == "__main__":
    sys.exit(main())
