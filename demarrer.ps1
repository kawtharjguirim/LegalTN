param(
    [ValidateRange(1, 65535)]
    [int]$Port = 8000,
    [ValidateSet("bm25", "hybride")]
    [string]$Moteur = "bm25"
)

$ErrorActionPreference = "Stop"
# Python du projet : venv Silver (env_silver.ps1), sinon .venv local, sinon python du PATH.
$Cache = if ($env:LEGALTN_CACHE) { $env:LEGALTN_CACHE } else { "D:\LegalTN-cache" }
$PythonProjet = Join-Path $Cache "venv\Scripts\python.exe"
if ($Moteur -eq "hybride") {
    . (Join-Path $PSScriptRoot "env_silver.ps1")
    $env:HF_HUB_OFFLINE = "1"
}
if (-not (Test-Path -LiteralPath $PythonProjet)) {
    $PythonProjet = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
}
if (-not (Test-Path -LiteralPath $PythonProjet)) {
    $PythonProjet = (Get-Command python -ErrorAction Stop).Source
}

Push-Location $PSScriptRoot
try {
    & $PythonProjet -X utf8 -B (Join-Path $PSScriptRoot "api.py") --port $Port --moteur $Moteur
    $CodeSortie = $LASTEXITCODE
}
finally {
    Pop-Location
}
exit $CodeSortie
