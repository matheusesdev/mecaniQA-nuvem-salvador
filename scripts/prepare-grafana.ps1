param(
    [switch]$ResetLocalCredentials
)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:KUBECONFIG = Join-Path (Get-Location) '.local/kubeconfig'
& "$PSScriptRoot/sync-grafana-config.ps1"
$existingSecret = & kubectl --context kind-mecaniqa -n mecaniqa get secret grafana-admin --ignore-not-found -o name
if ($LASTEXITCODE -ne 0) { throw 'Não foi possível consultar o Secret no cluster local.' }
if (!$existingSecret -or $ResetLocalCredentials) {
    # Public, didactic default for the local Kind environment.
    $password = 'MecaniQA@2026!'
    $secret = @{
        apiVersion = 'v1'; kind = 'Secret'
        metadata = @{ name = 'grafana-admin'; namespace = 'mecaniqa' }
        type = 'Opaque'
        stringData = @{ username = 'admin'; password = $password }
    } | ConvertTo-Json -Depth 5
    $secret | & kubectl --context kind-mecaniqa apply -f -
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar Secret do Grafana.' }
    if ($ResetLocalCredentials) {
        $deployment = & kubectl --context kind-mecaniqa -n mecaniqa get deployment grafana --ignore-not-found -o name
        if ($LASTEXITCODE -ne 0) { throw 'Falha ao consultar o Grafana.' }
        if ($deployment) {
            # The PVC already contains a user: changing its Secret alone does not reset it.
            $password | & kubectl --context kind-mecaniqa -n mecaniqa exec -i deployment/grafana -- grafana cli --homepath /usr/share/grafana --config /etc/grafana/grafana.ini admin reset-admin-password --password-from-stdin
            if ($LASTEXITCODE -ne 0) { throw 'Falha ao atualizar a senha persistida do Grafana.' }
        }
    }
    Write-Host 'Credencial padrão local configurada. Consulte o acesso no README.'
}
