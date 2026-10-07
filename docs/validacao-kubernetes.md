# Validação Kubernetes — MecaniQA Salvador

Última revisão: 06/10/2026. Recursos definidos em `k8s/`, no namespace `mecaniqa`.

## Arquitetura implementada

| Componente | Deployment | Service | Persistência |
| --- | --- | --- | --- |
| API Java | api, uma réplica | NodePort 30080, destino 8080 | Sem PVC |
| MySQL | mysql, uma réplica, Recreate | ClusterIP, mysql:3306 | mysql-data, 1 GiB em /var/lib/mysql |
| Redis | redis, uma réplica, Recreate | ClusterIP, redis:6379 | redis-data, 1 GiB em /data, AOF habilitado |

Os manifestos também definem o Namespace e o Secret `mysql-credentials`, com
senha didática. Todos os contêineres possuem requests/limits e probes.
A API recebe `DB_HOST=mysql` e `REDIS_HOST=redis`; `/health` verifica conexões
TCP, sem autenticar no banco, executar SQL ou comandos Redis.

No Kind, `infra/kind.yaml` mapeia a porta 30080 do nó para localhost:18080.
O script `scripts/deploy-local.ps1` constrói as imagens, cria ou reutiliza o
cluster, carrega as imagens e aplica os manifestos. Verifica por padrão 8 GiB
livres na unidade de LOCALAPPDATA; a reserva é ajustável por `MinimumFreeDiskGB`.

## Resultados de 06/10/2026

Os dez recursos passaram na validação pelo servidor e foram reaplicados ao
contexto `kind-mecaniqa`: Namespace, Secret, três Deployments, três Services
e dois PVCs. Os três Pods ficaram `1/1 Running`; os PVCs ficaram Bound.
O endpoint externo respondeu HTTP 200 com API, MySQL e Redis em UP.

O Metrics Server 0.8.1 foi instalado separadamente dos manifestos da aplicação.
A API de métricas ficou disponível; CPU e memória foram consultadas por kubectl
e exibidas no K9s. Pods e eventos foram inspecionados em modo readonly.
Não foi observado CrashLoopBackOff. Houve falhas transitórias de startup do
MySQL e readiness da API durante a retomada, seguidas por Pods prontos.

Os comandos, amostra das métricas e resultados de Docker/Compose estão em
[validacao-2026-10-06.md](validacao-2026-10-06.md).
Essa execução utilizou as imagens já carregadas no nó; as imagens reconstruídas
foram testadas no Docker e Compose, sem nova carga no Kind.

## Testes históricos de 10/09/2026

O registro anterior descreve Redis retornando PONG e MySQL retornando 1 em
`SELECT 1`. Para persistência, foi gravado `kubernetes-ok` na chave Redis
`validacao:persistencia` e na tabela MySQL `validacao_k8s`. Após reiniciar os
Deployments dos bancos, ambos devolveram o valor armazenado.

O registro também descreve a substituição do Pod da API
`api-df7f9b654-98dwz` por `api-df7f9b654-kjbp9` após sua exclusão,
com a nova réplica pronta e o endpoint novamente UP.
Esses dois testes não foram repetidos em 06/10; são resultados históricos.

## Comandos de inspeção

```powershell
$env:KUBECONFIG = Join-Path (Get-Location) '.local/kubeconfig'
kubectl --context kind-mecaniqa -n mecaniqa get deploy,pods,svc,pvc
kubectl --context kind-mecaniqa -n mecaniqa get endpointslices
kubectl --context kind-mecaniqa -n mecaniqa get events --sort-by=.metadata.creationTimestamp
kubectl --context kind-mecaniqa -n mecaniqa logs deployment/api --tail=50
kubectl --context kind-mecaniqa -n mecaniqa top pods
curl.exe --fail http://localhost:18080/health
.local/bin/k9s/k9s.exe --kubeconfig .local/kubeconfig --context kind-mecaniqa -n mecaniqa --readonly
```

No K9s, utilizar `:pods`, `:svc`, `:pvc` e `:events`, `l` para logs e `d` para
detalhes. As métricas representam uma amostra sem teste de carga.
Os PVCs preservam dados ao recriar Pods; no Kind, remover o cluster também
remove a persistência local do nó.
