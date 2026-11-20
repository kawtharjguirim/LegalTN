# Lance la démo Silver complète, après une vérification de tout ce dont elle dépend.
# Usage (PowerShell, depuis le dossier du projet) : .\demo_silver.ps1
#         (cmd) : powershell -ExecutionPolicy Bypass -File demo_silver.ps1
param(
    [int]$Port = 18765,
    [string]$Ollama = "D:\Ollama"
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "env_silver.ps1")
$env:HF_HUB_OFFLINE = "1"

function Etape($texte, $ok, $detail = "") {
    $marque = if ($ok) { "[OK]  " } else { "[!!]  " }
    $couleur = if ($ok) { "Green" } else { "Yellow" }
    Write-Host ($marque + $texte + $(if ($detail) { " - $detail" } else { "" })) -ForegroundColor $couleur
}

Write-Host "`n=== Vérifications avant la démo LegalTN Silver ===`n"

# 1. Python Silver
Etape "Python Silver" (Test-Path $Py) $Py

# 2. Carte graphique
$gpu = & nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader 2>$null
Etape "Carte graphique" ([bool]$gpu) "$gpu"

# 3. Ollama : démarrage si nécessaire
function OllamaRepond {
    try { Invoke-RestMethod -TimeoutSec 2 http://127.0.0.1:11434/api/tags } catch { $null }
}
$tags = OllamaRepond
if (-not $tags -and (Test-Path "$Ollama\ollama app.exe")) {
    Write-Host "      Démarrage d'Ollama..."
    Start-Process "$Ollama\ollama app.exe"
    for ($i = 0; $i -lt 20 -and -not $tags; $i++) { Start-Sleep 1; $tags = OllamaRepond }
}
Etape "Serveur Ollama" ([bool]$tags)
$modele = $tags.models | Where-Object { $_.name -eq "qwen2.5:3b" }
Etape "Modèle qwen2.5:3b" ([bool]$modele) $(if (-not $modele) { "lancer : ollama pull qwen2.5:3b" })

# 4. Modèles NER de démo
foreach ($m in "fr_xlmr", "ar_arabert") {
    Etape "Modèle NER $m" (Test-Path (Join-Path $PSScriptRoot "models\ner\$m")) $(if (-not (Test-Path (Join-Path $PSScriptRoot "models\ner\$m"))) { "voir DEMO_SILVER.md, préparation" })
}

# 5. Préchauffage du LLM (le premier appel charge le modèle sur la carte graphique)
if ($modele) {
    Write-Host "      Préchauffage du LLM..."
    $corps = @{ model = "qwen2.5:3b"; prompt = "Bonjour"; stream = $false; options = @{ num_predict = 1 } } | ConvertTo-Json
    try { Invoke-RestMethod -TimeoutSec 60 -Method Post http://127.0.0.1:11434/api/generate -Body $corps -ContentType "application/json" | Out-Null; Etape "LLM préchauffé" $true }
    catch { Etape "LLM préchauffé" $false $_.Exception.Message }
}

Write-Host "`n=== Démarrage de l'application : http://127.0.0.1:$Port/ ===`n"
Start-Job -ScriptBlock { param($p) Start-Sleep 25; Start-Process "http://127.0.0.1:$p/" } -ArgumentList $Port | Out-Null
& (Join-Path $PSScriptRoot "demarrer.ps1") -Port $Port -Moteur hybride
