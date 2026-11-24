[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$requirements = Join-Path $projectRoot "requirements.txt"

function Invoke-PythonCandidate {
    param(
        [Parameter(Mandatory)]
        [string]$Command,

        [string[]]$Arguments = @()
    )

    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
        return $null
    }

    $version = & $Command @Arguments -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
    if ($LASTEXITCODE -ne 0) {
        return $null
    }

    $parsedVersion = [version]$version
    if ($parsedVersion -lt [version]"3.10") {
        return $null
    }

    return @{
        Command   = $Command
        Arguments = $Arguments
    }
}

if (Test-Path $venvPython) {
    if (-not (Invoke-PythonCandidate -Command $venvPython)) {
        throw @"
The existing virtual environment does not use a supported Python version.
Remove '.venv', install Python 3.10 or newer, and rerun this script.
"@
    }
}
else {
    $python = Invoke-PythonCandidate -Command "py" -Arguments @("-3")
    if (-not $python) {
        $python = Invoke-PythonCandidate -Command "python"
    }
    if (-not $python) {
        $python = Invoke-PythonCandidate -Command "python3"
    }

    if (-not $python) {
        throw @"
Python 3.10 or newer was not found. Install Python 3, or disable a broken
Microsoft Store App Execution Alias in Settings > Apps > Advanced app settings
> App execution aliases, then rerun this script.
"@
    }

    Write-Host "Creating virtual environment with $($python.Command)..."
    & $python.Command @($python.Arguments) -m venv (Join-Path $projectRoot ".venv")
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create the virtual environment."
    }
}

if (-not (Test-Path $venvPython)) {
    throw "The virtual environment was created, but '$venvPython' was not found."
}

Write-Host "Installing dependencies..."
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "Failed to upgrade pip."
}

& $venvPython -m pip install -r $requirements
if ($LASTEXITCODE -ne 0) {
    throw "Failed to install project dependencies."
}

Write-Host "Setup complete. Run the application with '.\run.ps1 --list-devices'."
