$ErrorActionPreference = 'Stop'

$GameDir = Split-Path -Parent $PSScriptRoot
$GamesDir = Split-Path -Parent $GameDir
$SdkRoot = Split-Path -Parent $GamesDir

$SystemPython = Get-Command python -ErrorAction SilentlyContinue
if (-not $SystemPython) { throw 'Python was not found. Install Python 3.12 or newer and reopen PowerShell.' }
$SystemPythonVersion = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ([version]$SystemPythonVersion -lt [version]'3.12') {
    throw "Python 3.12 or newer is required. Found $SystemPythonVersion."
}

$VenvDir = Join-Path $SdkRoot '.venv'
if (-not (Test-Path $VenvDir)) {
    & python -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) { throw "python -m venv failed with exit code $LASTEXITCODE" }
}
$Python = Join-Path $VenvDir 'Scripts\python.exe'
if (-not (Test-Path $Python)) { throw "Virtual environment Python not found: $Python" }

Write-Host 'Installing the Math SDK pinned requirements...' -ForegroundColor Cyan
& $Python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed with exit code $LASTEXITCODE" }
& $Python -m pip install -r (Join-Path $SdkRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw "SDK requirements installation failed with exit code $LASTEXITCODE" }
& $Python -m pip install -e $SdkRoot
if ($LASTEXITCODE -ne 0) { throw "Editable SDK installation failed with exit code $LASTEXITCODE" }

$env:PYTHONPATH = "$GameDir;$SdkRoot"

Write-Host 'Checking the installed compression dependency...' -ForegroundColor Cyan
$ZstdVersion = & $Python -c "import zstandard; print(zstandard.__version__)"
if ($LASTEXITCODE -ne 0 -or $ZstdVersion -ne '0.23.0') {
    throw "Expected zstandard==0.23.0, found $ZstdVersion. Check the SDK requirements pin."
}

Write-Host 'Running Sewer Surge SDK contract check...' -ForegroundColor Cyan
& $Python (Join-Path $GameDir 'scripts\check_sdk_contract.py') --require-exact-pin
if ($LASTEXITCODE -ne 0) { throw "SDK contract check failed with exit code $LASTEXITCODE" }

Write-Host 'Running Sewer Surge tests...' -ForegroundColor Cyan
& $Python -m pytest (Join-Path $GameDir 'tests') -q
if ($LASTEXITCODE -ne 0) { throw "Sewer Surge tests failed with exit code $LASTEXITCODE" }

Write-Host 'Setup complete. Rust/Cargo are required before running run_production.ps1.' -ForegroundColor Green
