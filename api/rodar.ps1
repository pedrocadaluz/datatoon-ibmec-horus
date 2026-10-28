param([string]$Dados = "", [int]$Porta = 8000, [string]$HostApi = "0.0.0.0", [switch]$Preparar)
$ErrorActionPreference = 'Stop'
$raizProjeto = Split-Path -Parent $PSScriptRoot
$pythonLocal = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonLocal)) {
    python -m venv (Join-Path $PSScriptRoot '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 ou 3.13 é necessário para criar o ambiente.' }
}
& $pythonLocal -m pip install -r (Join-Path $raizProjeto 'requirements.txt') --disable-pip-version-check --quiet
if ($LASTEXITCODE -ne 0) { throw 'Não foi possível instalar as dependências da API.' }
if (-not $Dados) { $Dados = $env:CASA_GEMEA_DADOS }
if (-not $Dados) {
    $candidatos = @($raizProjeto,
        (Join-Path $env:USERPROFILE 'Downloads\Seguro_Residencial_DadosSinteticos\Seguro_Residencial_DadosSinteticos'),
        (Join-Path $env:USERPROFILE 'Downloads\Seguro_Residencial_DadosSinteticos'))
    foreach ($candidato in $candidatos) {
        if ((Test-Path -LiteralPath (Join-Path $candidato 'Seguro_Residencial_Desenvolvimento')) -and
            (Test-Path -LiteralPath (Join-Path $candidato 'Seguro_Residencial_Teste_Comum'))) {
            $Dados = $candidato
            break
        }
    }
}
if ($Dados) {
    $env:CASA_GEMEA_DADOS = (Resolve-Path -LiteralPath $Dados).Path
    Write-Host "Bases locais: $env:CASA_GEMEA_DADOS"
}
if ($Preparar) { return }
Push-Location -LiteralPath $raizProjeto
try { & $pythonLocal -m uvicorn api.main:app --host $HostApi --port $Porta }
finally { Pop-Location }
