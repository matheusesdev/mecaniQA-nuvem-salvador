$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:KUBECONFIG = Join-Path (Get-Location) '.local/kubeconfig'
& "$PSScriptRoot/sync-grafana-config.ps1"
$existingSecret = & kubectl --context kind-mecaniqa -n mecaniqa get secret grafana-admin --ignore-not-found -o name
if ($LASTEXITCODE -ne 0) { throw 'Não foi possível consultar o Secret no cluster local.' }
if (!$existingSecret) {
    $password = [Guid]::NewGuid().ToString('N')
    $secret = @{
        apiVersion = 'v1'; kind = 'Secret'
        metadata = @{ name = 'grafana-admin'; namespace = 'mecaniqa' }
        type = 'Opaque'
        stringData = @{ username = 'admin'; password = $password }
    } | ConvertTo-Json -Depth 5
    $secret | & kubectl --context kind-mecaniqa apply -f -
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar Secret do Grafana.' }
    Write-Host 'Credencial gerada e armazenada somente no Secret do cluster.'
}
