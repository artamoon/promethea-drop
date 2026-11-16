# Build the local, unsigned preview installer after building dist/PrometheaDrop.
param(
    [string]$Compiler = $env:INNO_ISCC,
    [string]$BuildDir = ""
)
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not $BuildDir) { $BuildDir = Join-Path $projectRoot "dist\PrometheaDrop" }
if (-not (Test-Path -LiteralPath (Join-Path $BuildDir "PrometheaDrop.exe"))) {
    throw "Application build not found: $BuildDir"
}
if (-not $Compiler) {
    $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($cmd) { $Compiler = $cmd.Source }
}
if (-not $Compiler) {
    $candidates = @(
        (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
        (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
    )
    $Compiler = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (-not $Compiler -or -not (Test-Path -LiteralPath $Compiler)) {
    throw "Inno Setup compiler not found; pass -Compiler or set INNO_ISCC."
}
$script = Join-Path $projectRoot "installer\PROMETHEA Drop.iss"
& $Compiler "/DBuildDir=$((Resolve-Path -LiteralPath $BuildDir).Path)" $script
if ($LASTEXITCODE -ne 0) { throw "Installer compilation failed: $LASTEXITCODE" }
