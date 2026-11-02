param(
    [int]$Simulations = 100000,
    [int]$Threads = 10,
    [int]$RustThreads = 10,
    [int]$BatchSize = 25000
)

$ErrorActionPreference = 'Stop'
$GameDir = Split-Path -Parent $PSScriptRoot
$GamesDir = Split-Path -Parent $GameDir
$SdkRoot = Split-Path -Parent $GamesDir
$Python = Join-Path $SdkRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $Python)) {
    throw "The SDK virtual environment is missing. Run scripts\setup_windows.ps1 first."
}
if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    throw 'Rust/Cargo is required for the optimizer. Install from https://rustup.rs/ and reopen PowerShell.'
}
if (-not (Get-Command rustc -ErrorAction SilentlyContinue)) {
    throw 'rustc was not found. Repair the Rust toolchain before proceeding.'
}
$ZstdVersion = & $Python -c "import zstandard; print(zstandard.__version__)"
if ($LASTEXITCODE -ne 0 -or $ZstdVersion -ne '0.23.0') {
    throw "Expected zstandard==0.23.0, found $ZstdVersion. Rerun setup_windows.ps1."
}

$env:PYTHONPATH = "$GameDir;$SdkRoot"
& $Python (Join-Path $GameDir 'scripts\check_sdk_contract.py') --require-exact-pin
if ($LASTEXITCODE -ne 0) { throw "Exact SDK pin/contract check failed with exit code $LASTEXITCODE" }
& $Python (Join-Path $GameDir 'run.py') `
    --sims $Simulations `
    --threads $Threads `
    --rust-threads $RustThreads `
    --batch-size $BatchSize `
    --compress --clean --optimize --verify
if ($LASTEXITCODE -ne 0) { throw "Math SDK generation/optimization/verifier failed with exit code $LASTEXITCODE" }

$env:SEWER_SURGE_AUDIT_OUTPUT = Join-Path $GameDir 'library\audit-summary.json'
& $Python (Join-Path $GameDir 'scripts\audit_all_modes.py') --require-optimized-lut --target-rtp 96.5 --tolerance 0.5
if ($LASTEXITCODE -ne 0) { throw "Four-mode structural/optimized-LUT audit failed with exit code $LASTEXITCODE" }

Write-Host "Production workflow and weighted-LUT audit completed. Review $env:SEWER_SURGE_AUDIT_OUTPUT before upload." -ForegroundColor Green
