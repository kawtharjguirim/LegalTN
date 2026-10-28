param(
    [ValidateRange(1, 65535)]
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$PythonProjet = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $PythonProjet)) {
    $PythonProjet = (Get-Command python -ErrorAction Stop).Source
}

Push-Location $PSScriptRoot
try {
    & $PythonProjet -X utf8 -B (Join-Path $PSScriptRoot "api.py") --port $Port
    $CodeSortie = $LASTEXITCODE
}
finally {
    Pop-Location
}
exit $CodeSortie
