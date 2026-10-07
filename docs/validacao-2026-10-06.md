# Validação da OAT 1 — 06/10/2026

Inspeção concluída aproximadamente às 21h07, horário de São Paulo.
Branch: `validacao-entregas-oat1-2026-10-06`.

## Docker e testes isolados

Docker Engine: 29.7.2. Os três comandos terminaram com imagens exportadas:

```powershell
docker build -t mecaniqa-api:encontro1 ./api
docker build -t mecaniqa-mysql:encontro1 ./mysql
docker build -t mecaniqa-redis:encontro1 ./redis
```

Foram criados contêineres de teste com nomes `oat1-validacao-api`,
`oat1-validacao-mysql` e `oat1-validacao-redis`. A API foi publicada em 18081;
os bancos foram testados por `docker exec`, sem publicar suas portas.

| Teste | Resultado observado |
| --- | --- |
| API isolada, GET `localhost:18081/health` | HTTP 503; status DOWN, mysql DOWN, redis DOWN, conforme esperado sem dependências acessíveis. |
| MySQL, `SELECT 1 AS teste` no banco mecaniqa | Retornou 1; health check healthy. |
| Redis, `redis-cli ping` | PONG; health check healthy. |
| Health check da API isolada | unhealthy, pois usa o endpoint dependente dos bancos. |

Após os testes, os três contêineres temporários foram parados e removidos.
Não foram removidos volumes.

## Docker Compose

```powershell
docker compose up --build -d --wait --wait-timeout 120
docker compose ps
curl.exe -s -i --max-time 10 http://localhost:8080/health
```

O comando terminou com sucesso. Os três serviços ficaram healthy.
O endpoint retornou HTTP 200 e:

```json
{"status":"UP","service":"mecaniqa-api","mysql":"UP","redis":"UP"}
```

O ambiente Compose permanece ativo com seus volumes nomeados.

## Kubernetes e K9s

Contexto `kind-mecaniqa`, Kubernetes v1.34.0, namespace `mecaniqa`.
Os dez recursos de `k8s/` passaram por `apply --dry-run=server` e foram
reaplicados. Os três Deployments ficaram disponíveis; os três Pods ficaram
`1/1 Running`, com um reinício registrado por Pod após a retomada do Docker.
Os dois PVCs ficaram Bound, com 1 GiB cada.
GET `localhost:18080/health` retornou HTTP 200 com todos os componentes UP.

O Metrics Server 0.8.1 foi instalado pelo manifesto oficial. No Kind local,
foi acrescentado `--kubelet-insecure-tls` ao Deployment do Metrics Server.
Esse ajuste ignora a validação do certificado do kubelet e está restrito à
demonstração local; não é configuração de produção.

Comandos para reproduzir a instalação no contexto local:

```powershell
$env:KUBECONFIG = Join-Path (Get-Location) '.local/kubeconfig'
kubectl --context kind-mecaniqa apply -f https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.8.1/components.yaml
kubectl --context kind-mecaniqa -n kube-system edit deployment metrics-server
# Acrescentar --kubelet-insecure-tls na lista args do contêiner metrics-server, somente no Kind local.
kubectl --context kind-mecaniqa -n kube-system rollout status deployment/metrics-server
kubectl --context kind-mecaniqa get apiservice v1beta1.metrics.k8s.io
kubectl --context kind-mecaniqa -n mecaniqa top pods
```

A APIService apresentou AVAILABLE=True. Amostra de `top pods`, também exibida
na tela de Pods do K9s v0.51.0:

| Pod | CPU | Memória |
| --- | --- | --- |
| api-df7f9b654-nnd6l | 2m | 19Mi |
| mysql-755dc77787-vcpbx | 11m | 449Mi |
| redis-8696fc58f-tw8zx | 6m | 6Mi |

Os valores são uma amostra do ambiente sem teste de carga; não comprovam
capacidade em produção ou ausência de gargalos sob carga.

K9s aberto em modo readonly, contexto kind-mecaniqa e namespace mecaniqa.
Foram inspecionadas as telas `:pods` e `:events`, e a sessão foi encerrada com `:q`.
Nenhum Pod em CrashLoopBackOff foi observado. Eventos mostraram falhas transitórias
de startup do MySQL e readiness da API durante a retomada; depois, os três Pods
ficaram prontos. Não foi necessário provocar falhas nem coletar logs de CrashLoopBackOff.

Persistência após recriação e substituição automática da API não foram repetidas
nesta execução; seus resultados anteriores estão em `validacao-kubernetes.md`.
As imagens novas foram testadas no Docker/Compose; o cluster foi validado com
as imagens já carregadas no nó, sem substituí-las nesta execução.

Fonte da instalação: [Metrics Server oficial](https://github.com/kubernetes-sigs/metrics-server).
