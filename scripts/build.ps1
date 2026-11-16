# Сборка PROMETHEA Drop.
#
#   .\scripts\build.ps1                 # onedir (рекомендуется: меньше ложных срабатываний)
#   .\scripts\build.ps1 -OneFile        # один exe (удобно, но эвристики реагируют чаще)
#   .\scripts\build.ps1 -Sign <thumbprint>   # подписать результат сертификатом из хранилища
#
# Подпись требует Windows SDK (signtool.exe) и сертификата Code Signing.

param(
    [switch]$OneFile,
    [string]$Sign = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$python = Join-Path $root ".venv\Scripts\pyinstaller.exe"
if (-not (Test-Path $python)) { throw "нет $python — сначала создайте venv и поставьте зависимости" }

Push-Location $root
try {
    if ($OneFile) { $env:ONEFILE = "1" } else { Remove-Item Env:\ONEFILE -ErrorAction SilentlyContinue }
    & $python Promethea.spec --noconfirm
    if ($LASTEXITCODE -ne 0) { throw "pyinstaller завершился с кодом $LASTEXITCODE" }

    $targets = if ($OneFile) {
        @(Join-Path $root "dist\PrometheaDrop.exe")
    } else {
        @(Join-Path $root "dist\PrometheaDrop\PrometheaDrop.exe")
    }

    if ($Sign) {
        $signtool = Get-Command signtool.exe -ErrorAction SilentlyContinue
        if (-not $signtool) { throw "signtool.exe не найден: установите Windows SDK" }
        foreach ($file in $targets) {
            & $signtool.Source sign /sha1 $Sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 $file
            if ($LASTEXITCODE -ne 0) { throw "подпись не удалась: $file" }
        }
    }

    foreach ($file in $targets) {
        if (Test-Path $file) {
            $hash = (Get-FileHash $file -Algorithm SHA256).Hash
            $size = [math]::Round((Get-Item $file).Length / 1MB, 1)
            Write-Host "готово: $file ($size МБ)"
            Write-Host "sha256: $hash"
            Write-Host "подпись: $(if ($Sign) { 'есть' } else { 'нет — для распространения нужен сертификат' })"
        }
    }
    Write-Host "проверка: dist\PrometheaDrop\PrometheaDrop.exe --selftest"
}
finally {
    Pop-Location
}
