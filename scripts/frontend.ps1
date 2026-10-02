param([ValidateSet('dev','build','start','install')][string]$Action='dev')
$projectRoot=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath "$projectRoot/frontend"
$npmCommand=Get-Command npm -ErrorAction SilentlyContinue
if ($npmCommand) {
    if ($Action -eq 'install') { & $npmCommand.Source install }
    elseif ($Action -eq 'start') { & $npmCommand.Source start }
    else { & $npmCommand.Source run $Action }
} else {
    $pnpmPath=Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/fallback/pnpm.cmd'
    if (!(Test-Path -LiteralPath $pnpmPath)) { throw 'Install Node.js with npm, or use the Codex bundled pnpm runtime.' }
    if ($Action -eq 'install') { & $pnpmPath install --store-dir '../work/pnpm-store' }
    else { & $pnpmPath run $Action }
}
