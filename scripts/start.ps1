param([switch]$Fallback)
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if ($Fallback) { $env:SENTIMENT_MODE = 'fallback' }
$env:HF_HOME = Join-Path $projectRoot '.models'
if (!(Test-Path -LiteralPath '.venv/Scripts/python.exe')) { throw 'Install dependencies using the README Quickstart first.' }
New-Item -ItemType Directory -Path work -Force | Out-Null
Start-Process -FilePath "$projectRoot/.venv/Scripts/python.exe" -ArgumentList '-m','uvicorn','backend.main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput "$projectRoot/work/backend.log" -RedirectStandardError "$projectRoot/work/backend-error.log"
Write-Host 'Backend starting at http://127.0.0.1:8000. In a second terminal: cd frontend; npm run dev'
