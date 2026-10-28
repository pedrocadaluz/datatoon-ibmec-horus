param(
    [string]$Dados = "",
    [ValidateRange(1024, 65535)][int]$PortaWeb = 5173,
    [ValidateRange(1024, 65535)][int]$PortaApi = 8000,
    [string]$Certificado = "",
    [string]$Chave = "",
    [switch]$Verificar
)
$ErrorActionPreference = 'Stop'
$raizProjeto = Split-Path -Parent $PSScriptRoot
$pastaWeb = Join-Path $raizProjeto 'web'
$processoApi = $null
$processoWeb = $null
if ($PortaWeb -eq $PortaApi) { throw 'Use portas diferentes para API e aplicação.' }
foreach ($portaAtual in @($PortaWeb, $PortaApi)) {
    if (Get-NetTCPConnection -LocalPort $portaAtual -State Listen -ErrorAction SilentlyContinue) {
        throw "Porta $portaAtual em uso. Feche a execução anterior ou use -PortaWeb e -PortaApi livres."
    }
}
if ([bool]$Certificado -ne [bool]$Chave) { throw 'Informe -Certificado e -Chave juntos.' }
$protocolo = 'http'
if ($Certificado) {
    $env:HORUS_HTTPS_CERT = (Resolve-Path -LiteralPath $Certificado).Path
    $env:HORUS_HTTPS_KEY = (Resolve-Path -LiteralPath $Chave).Path
    $protocolo = 'https'
} else {
    Remove-Item Env:HORUS_HTTPS_CERT -ErrorAction SilentlyContinue
    Remove-Item Env:HORUS_HTTPS_KEY -ErrorAction SilentlyContinue
}
$ipsRede = @(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.AddressState -eq 'Preferred' -and ($_.IPAddress -match '^10\.' -or $_.IPAddress -match '^192\.168\.' -or $_.IPAddress -match '^172\.(1[6-9]|2[0-9]|3[01])\.') } |
    Sort-Object InterfaceMetric, InterfaceIndex | Select-Object -ExpandProperty IPAddress -Unique)
$env:HORUS_LOCAL_IPS = $ipsRede -join ','
$env:HORUS_WEB_PORT = "$PortaWeb"
$env:HORUS_API_PORT = "$PortaApi"
& (Join-Path $raizProjeto 'api\rodar.ps1') -Dados $Dados -Porta $PortaApi -Preparar
$npm = (Get-Command npm.cmd).Source
$node = (Get-Command node.exe).Source
Push-Location -LiteralPath $pastaWeb
try {
    & $npm ci --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível preparar o frontend.' }
    & $npm run build
    if ($LASTEXITCODE -ne 0) { throw 'Build do frontend falhou.' }
} finally { Pop-Location }
try {
    $python = Join-Path $raizProjeto 'api\.venv\Scripts\python.exe'
    $vite = Join-Path $pastaWeb 'node_modules\vite\bin\vite.js'
    $processoApi = Start-Process -FilePath $python -ArgumentList @('-m', 'uvicorn', 'api.main:app', '--host', '0.0.0.0', '--port', "$PortaApi") -WorkingDirectory $raizProjeto -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $raizProjeto 'api\rede-api.log') -RedirectStandardError (Join-Path $raizProjeto 'api\rede-api-erro.log')
    $processoWeb = Start-Process -FilePath $node -ArgumentList @(('"{0}"' -f $vite), 'preview', '--host', '0.0.0.0', '--port', "$PortaWeb") -WorkingDirectory $pastaWeb -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $pastaWeb 'rede-web.log') -RedirectStandardError (Join-Path $pastaWeb 'rede-web-erro.log')
    $limite = (Get-Date).AddSeconds(35)
    $apiPronta = $false
    $webPronta = $false
    while ((Get-Date) -lt $limite) {
        if ($processoApi.HasExited -or $processoWeb.HasExited) { throw 'Um servidor encerrou. Veja api/rede-api-erro.log e web/rede-web-erro.log.' }
        try { $null = Invoke-RestMethod "http://127.0.0.1:$PortaApi/api/health" -TimeoutSec 2; $apiPronta = $true } catch { $apiPronta = $false }
        $webPronta = [bool](Get-NetTCPConnection -LocalPort $PortaWeb -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -eq $processoWeb.Id })
        if ($apiPronta -and $webPronta) { break }
        Start-Sleep -Milliseconds 300
    }
    if (-not $apiPronta) { throw 'O motor não ficou pronto. Confira os caminhos das bases e api/rede-api-erro.log.' }
    if (-not $webPronta) { throw 'A aplicação não ficou pronta. Confira web/rede-web-erro.log.' }
    Write-Host "`nCasa Gêmea pronta. Ctrl+C encerra os dois processos desta execução." -ForegroundColor Green
    Write-Host "Computador: ${protocolo}://localhost:$PortaWeb"
    foreach ($ip in $ipsRede) { Write-Host "Celular:    ${protocolo}://${ip}:$PortaWeb" -ForegroundColor Cyan }
    Write-Host "QR code:    ${protocolo}://localhost:$PortaWeb/celular"
    if (-not $ipsRede.Count) { Write-Host 'Conecte o computador a uma rede Wi-Fi privada para obter o endereço do celular.' }
    if ($protocolo -eq 'http') { Write-Host 'HTTP permite demonstrar no navegador. Instalação offline no telefone exige HTTPS local confiável, conforme web/README.md.' }
    if ($Verificar) { Write-Host 'Verificação concluída. Encerrando os processos desta execução.'; return }
    while (-not ($processoApi.HasExited -or $processoWeb.HasExited)) { Start-Sleep -Seconds 1 }
} finally {
    foreach ($processo in @($processoWeb, $processoApi)) {
        # O Python do venv usa um launcher no Windows. A árvore pertence ao
        # processo que acabamos de iniciar, nunca ao ocupante arbitrário de uma porta.
        if ($processo -and -not $processo.HasExited) {
            & "$env:SystemRoot\System32\taskkill.exe" /PID $processo.Id /T /F 2>$null | Out-Null
        }
    }
}
