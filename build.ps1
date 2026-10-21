$ErrorActionPreference = "Stop"

python -m pip install -r requirements-dev.txt
python -m PyInstaller --noconfirm --clean --onefile --windowed --distpath release --name "Macro Play" --collect-all pynput run.py

Write-Host "Build complete: release\Macro Play.exe" -ForegroundColor Green

