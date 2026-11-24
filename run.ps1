[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments)]
    [string[]]$ScriptArguments
)

$ErrorActionPreference = "Stop"
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$script = Join-Path $PSScriptRoot "live_en_es.py"

if (-not (Test-Path $venvPython)) {
    throw "The project virtual environment was not found. Run '.\setup.ps1' first."
}

$pythonVersion = & $venvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "The virtual environment's Python interpreter could not be started. Rerun '.\setup.ps1'."
}

$parsedVersion = [version]$pythonVersion
if ($parsedVersion -lt [version]"3.10") {
    throw "The project requires Python 3.10 or newer. Recreate '.venv' with a supported version."
}

& $venvPython $script @ScriptArguments
exit $LASTEXITCODE
