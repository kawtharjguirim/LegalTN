# Environnement du palier Silver. À charger avant toute commande : . .\env_silver.ps1
# Le disque C étant presque plein, l'environnement Python, les caches et les modèles
# sont placés sur D. Changer $Cache pour une autre machine.
$Cache = if ($env:LEGALTN_CACHE) { $env:LEGALTN_CACHE } else { "D:\LegalTN-cache" }
New-Item -ItemType Directory -Force "$Cache\tmp", "$Cache\pip", "$Cache\hf" | Out-Null
$env:TMP = "$Cache\tmp"
$env:TEMP = "$Cache\tmp"
$env:PIP_CACHE_DIR = "$Cache\pip"
$env:HF_HOME = "$Cache\hf"
$env:PYTHONUTF8 = "1"
$Py = "$Cache\venv\Scripts\python.exe"
Write-Host "LegalTN Silver : python = $Py ; HF_HOME = $env:HF_HOME"
