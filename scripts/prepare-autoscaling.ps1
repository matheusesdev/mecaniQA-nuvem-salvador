$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$env:KUBECONFIG = Join-Path $root '.local/kubeconfig'
function Run([string[]]$Arguments) {
    & kubectl --context kind-mecaniqa @Arguments
    if ($LASTEXITCODE -ne 0) { throw "kubectl falhou: $Arguments" }
}
# Kind only: kubelet certificates do not have trusted IP SANs.
Run @('apply', '-f', 'https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.8.1/components.yaml')
$patch = Join-Path $root '.local/metrics-server-patch.json'
[IO.File]::WriteAllText($patch, '[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]')
$deployment = & kubectl --context kind-mecaniqa -n kube-system get deployment metrics-server -o json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'Metrics Server indisponível.' }
if ($deployment.spec.template.spec.containers[0].args -notcontains '--kubelet-insecure-tls') {
    Run @('-n', 'kube-system', 'patch', 'deployment', 'metrics-server', '--type=json', '--patch-file', $patch)
}
Run @('-n', 'kube-system', 'rollout', 'status', 'deployment/metrics-server', '--timeout=180s')
Run @('wait', 'apiservice/v1beta1.metrics.k8s.io', '--for=condition=Available', '--timeout=180s')
Run @('-n', 'mecaniqa', 'top', 'pods')
