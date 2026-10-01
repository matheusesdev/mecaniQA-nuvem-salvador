param(
    [ValidateRange(1, 1024)]
    [double]$MinimumFreeDiskGB = 8
)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$kind = Join-Path (Get-Location) '.local/bin/kind.exe'
if (!(Test-Path $kind)) { throw 'Instale Kind em .local/bin/kind.exe conforme README.md.' }
$env:KUBECONFIG = Join-Path (Get-Location) '.local/kubeconfig'
function Run {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Falha ao executar $Program $Arguments" }
}
function Assert-DiskSpace {
    # Docker Desktop usa LOCALAPPDATA para seu disco virtual na instalação local.
    $drive = [IO.DriveInfo]::new([IO.Path]::GetPathRoot($env:LOCALAPPDATA))
    if ($drive.AvailableFreeSpace -lt ($MinimumFreeDiskGB * 1GB)) {
        $freeGB = [Math]::Round($drive.AvailableFreeSpace / 1GB, 2)
        throw "Espaço insuficiente em $($drive.Name): $freeGB GiB livres. Libere ao menos $MinimumFreeDiskGB GiB antes de continuar."
    }
}
Assert-DiskSpace
foreach ($service in @('api', 'mysql', 'redis')) {
    Run docker @('build', '-t', "mecaniqa-${service}:encontro1", "./$service")
}
Assert-DiskSpace
$clusters = & $kind get clusters
if ($LASTEXITCODE -ne 0) { throw 'Não foi possível consultar os clusters Kind.' }
if ($clusters -notcontains 'mecaniqa') {
    Run $kind @('create', 'cluster', '--name', 'mecaniqa', '--config', 'infra/kind.yaml', '--kubeconfig', $env:KUBECONFIG, '--wait', '180s')
} else {
    Run $kind @('export', 'kubeconfig', '--name', 'mecaniqa', '--kubeconfig', $env:KUBECONFIG)
}
Assert-DiskSpace
foreach ($service in @('api', 'mysql', 'redis')) {
    Run $kind @('load', 'docker-image', '--name', 'mecaniqa', "mecaniqa-${service}:encontro1")
}
Run kubectl @('--context', 'kind-mecaniqa', 'apply', '-f', 'k8s/namespace.yaml')
Run kubectl @('--context', 'kind-mecaniqa', 'apply', '--dry-run=server', '-f', 'k8s/')
Run kubectl @('--context', 'kind-mecaniqa', 'apply', '-f', 'k8s/')
foreach ($service in @('mysql', 'redis', 'api')) {
    Run kubectl @('--context', 'kind-mecaniqa', '-n', 'mecaniqa', 'rollout', 'status', "deployment/$service", '--timeout=300s')
}
Run kubectl @('--context', 'kind-mecaniqa', '-n', 'mecaniqa', 'get', 'deploy,pods,svc,pvc')
$health = Invoke-RestMethod 'http://localhost:18080/health'
if ($health.status -ne 'UP' -or $health.mysql -ne 'UP' -or $health.redis -ne 'UP') { throw 'API ou dependências indisponíveis.' }
$health | ConvertTo-Json -Compress
