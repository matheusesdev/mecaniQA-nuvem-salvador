param(
    [string]$GrafanaUrl = 'http://localhost:3000',
    [string]$PrometheusUrl = 'http://localhost:9090'
)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:KUBECONFIG = Join-Path (Get-Location) '.local/kubeconfig'
$secretRaw = & kubectl --context kind-mecaniqa -n mecaniqa get secret grafana-admin -o json
if ($LASTEXITCODE -ne 0) { throw 'Falha ao obter credenciais do cluster local.' }
$secretData = ($secretRaw -join "`n" | ConvertFrom-Json).data
$username = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($secretData.username))
$password = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($secretData.password))
$authBytes = [Text.Encoding]::UTF8.GetBytes("${username}:$password")
$headers = @{ Authorization = 'Basic ' + [Convert]::ToBase64String($authBytes) }
$health = Invoke-RestMethod "$GrafanaUrl/api/health"
if ($health.database -ne 'ok') { throw 'Banco interno do Grafana indisponível.' }
$sourceHealth = Invoke-RestMethod "$GrafanaUrl/api/datasources/uid/mecaniqa-prometheus/health" -Headers $headers
if ($sourceHealth.status -ne 'OK') { throw 'Fonte Prometheus indisponível no Grafana.' }
$search = Invoke-RestMethod "$GrafanaUrl/api/search?type=dash-db&tag=oat2" -Headers $headers
if ($search.Count -ne 4) { throw "Esperados 4 dashboards; encontrados $($search.Count)." }
$evidencePath = Join-Path (Get-Location) 'docs/evidencias/2026-10-14'
New-Item -ItemType Directory -Force $evidencePath | Out-Null
$utf8 = [Text.UTF8Encoding]::new($false)
$queryResults = @()
$exports = @()
foreach ($file in (Get-ChildItem grafana/dashboards -Filter '*.json' | Sort-Object Name)) {
    $expected = Get-Content $file.FullName -Raw -Encoding utf8 | ConvertFrom-Json
    $loaded = Invoke-RestMethod "$GrafanaUrl/api/dashboards/uid/$($expected.uid)" -Headers $headers
    if ($loaded.dashboard.panels.Count -ne 1 -or
        $loaded.dashboard.panels[0].targets[0].expr -ne $expected.panels[0].targets[0].expr) {
        throw "Dashboard divergente: $($expected.uid)"
    }
    $exports += $loaded.dashboard
    # Janela fixa para conferir a consulta fora do mecanismo de variáveis do Grafana.
    $query = $expected.panels[0].targets[0].expr.Replace('$__rate_interval', '1m')
    $result = Invoke-RestMethod "$PrometheusUrl/api/v1/query?query=$([Uri]::EscapeDataString($query))"
    if ($result.status -ne 'success' -or $result.data.result.Count -eq 0) {
        throw "Consulta sem amostras: $query. Aguarde a coleta e repita."
    }
    $queryResults += @{ dashboard = $expected.uid; query = $query; response = $result }
}
$up = Invoke-RestMethod "$PrometheusUrl/api/v1/query?query=$([Uri]::EscapeDataString('up{job="iot-simulator"}'))"
if ($up.data.result.Count -ne 1 -or $up.data.result[0].value[1] -ne '1') { throw 'Scrape do simulador indisponível.' }
$evidence = [ordered]@{
    observed_at = [DateTimeOffset]::Now.ToString('o')
    grafana_health = $health; datasource_health = $sourceHealth
    dashboards = $search; queries = $queryResults; simulator_up = $up
}
[IO.File]::WriteAllText((Join-Path $evidencePath 'validacao-api.json'), ($evidence | ConvertTo-Json -Depth 30) + "`n", $utf8)
[IO.File]::WriteAllText((Join-Path $evidencePath 'dashboards-exportados.json'), (ConvertTo-Json -InputObject $exports -Depth 40) + "`n", $utf8)
Write-Host 'Grafana saudável; fonte Prometheus OK; quatro dashboards conferidos; quatro consultas com dados; scrape UP.'
Write-Host 'Evidências e exportação dos dashboards implantados salvas em docs/evidencias/2026-10-14/.'
