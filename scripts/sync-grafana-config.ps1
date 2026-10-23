$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$utf8 = [System.Text.UTF8Encoding]::new($false)
$resources = @(
    @{ Name = 'grafana-provisioning'; Files = @(
        @{ Key = 'prometheus.yaml'; Path = 'grafana/provisioning/datasources/prometheus.yaml' },
        @{ Key = 'provider.yaml'; Path = 'grafana/provisioning/dashboards/provider.yaml' },
        @{ Key = 'alerts.yaml'; Path = 'grafana/provisioning/alerting/alerts.yaml' }
    ) },
    @{ Name = 'grafana-dashboards'; Files = @(
        Get-ChildItem (Join-Path $projectRoot 'grafana/dashboards') -Filter '*.json' |
            Sort-Object Name | ForEach-Object { @{ Key = $_.Name; Path = $_.FullName } }
    ) }
)
$documents = foreach ($resource in $resources) {
    $lines = @('apiVersion: v1', 'kind: ConfigMap', 'metadata:',
        "  name: $($resource.Name)", '  namespace: mecaniqa', 'data:')
    foreach ($file in $resource.Files) {
        $sourcePath = if ([IO.Path]::IsPathRooted($file.Path)) { $file.Path } else { Join-Path $projectRoot $file.Path }
        $content = [IO.File]::ReadAllText($sourcePath).TrimEnd()
        if ($file.Key.EndsWith('.json')) { $null = $content | ConvertFrom-Json }
        $lines += "  $($file.Key): |"
        $lines += ($content -split '\r?\n' | ForEach-Object {
            if ([string]::IsNullOrWhiteSpace($_)) { '' } else { "    $($_.TrimEnd())" }
        })
    }
    $lines -join "`n"
}
[IO.File]::WriteAllText((Join-Path $projectRoot 'k8s/grafana-configmaps.yaml'), ($documents -join "`n---`n") + "`n", $utf8)
Write-Host 'ConfigMaps sincronizados a partir dos arquivos em grafana/.'
