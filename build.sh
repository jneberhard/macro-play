#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install -r requirements-dev.txt
python3 -m PyInstaller --noconfirm --clean --onefile --windowed --distpath release --name "Macro Play" --collect-all pynput run.py

echo "Build complete: release/Macro Play"

