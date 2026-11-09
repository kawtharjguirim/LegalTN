# Installe (si besoin) et lance LegalTN : API + interface web sur http://127.0.0.1:<Port>
# Usage : .\demarrer.ps1 [-Port 8000]
param(
    [ValidateRange(1, 65535)]
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$Venv = Join-Path $PSScriptRoot ".venv"
$PythonProjet = Join-Path $Venv "Scripts\python.exe"

function Test-Python([string]$Exe) {
    # Vrai si l'exécutable fonctionne et vaut Python 3.11 ou plus.
    if (-not (Test-Path -LiteralPath $Exe)) { return $false }
    # Un .venv copié d'une autre machine écrit sur stderr : ne pas en faire une erreur fatale.
    $ErrorActionPreference = "Continue"
    try {
        & $Exe -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

if (-not (Test-Python $PythonProjet)) {
    $Systeme = (Get-Command python -ErrorAction Stop).Source
    if (-not (Test-Python $Systeme)) { throw "Python 3.11 ou plus est requis ($Systeme)." }
    Write-Host "Création de l'environnement local .venv ..."
    # --clear : remplace un .venv existant mais inutilisable (créé sur une autre machine).
    & $Systeme -m venv --clear $Venv
    if ($LASTEXITCODE -ne 0) { throw "Échec de la création de .venv." }
}

Write-Host "Vérification des dépendances (requirements.txt) ..."
& $PythonProjet -m pip install --disable-pip-version-check -q -r (Join-Path $PSScriptRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Échec de l'installation des dépendances." }

Push-Location $PSScriptRoot
try {
    & $PythonProjet -X utf8 -B (Join-Path $PSScriptRoot "api.py") --port $Port
    $CodeSortie = $LASTEXITCODE
}
finally {
    Pop-Location
}
exit $CodeSortie
