# Run from a normal user terminal if the Codex sandbox blocks .git writes.
$projectRoot=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$gitExe=(Get-Command git -ErrorAction SilentlyContinue).Source
if (!$gitExe) { $gitExe='C:\Users\Sudhanshu\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe' }
if (!(Test-Path -LiteralPath $gitExe)) { throw 'Git is required.' }
if (!(Test-Path -LiteralPath '.git')) { & $gitExe init -b main; if ($LASTEXITCODE) { throw 'Git initialization failed' } }
$existing=& $gitExe remote get-url origin 2>$null
if (!$existing) { & $gitExe remote add origin 'https://github.com/sahsudhanshu/SP.git' }
elseif ($existing -ne 'https://github.com/sahsudhanshu/SP.git') { throw 'Existing origin differs; review before publishing.' }
& $gitExe -c http.sslBackend=openssl add .
if ($LASTEXITCODE) { throw 'Could not stage project files' }
& $gitExe diff --cached --quiet
if ($LASTEXITCODE -eq 1) { & $gitExe commit -m 'Implement RiskPulse AI with verified NLP, stress tests and submission materials' }
& $gitExe -c http.sslBackend=openssl push -u origin main
if ($LASTEXITCODE) { throw 'Push failed. Check GitHub authentication and remote history; no force push is attempted.' }
Write-Host 'Pushed to https://github.com/sahsudhanshu/SP'
