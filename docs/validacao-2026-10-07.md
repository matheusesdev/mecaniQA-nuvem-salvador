# Validação inicial de métricas IoT — 07/10/2026

Execução local no Windows, em 07/10/2026 (horário de São Paulo), na branch
`entrega-monitoramento-prometheus`. Python local: 3.14.3; Docker Engine: 29.4.2.
O contêiner usa Python 3.13 slim.

## Verificações concluídas

| Verificação | Resultado observado |
| --- | --- |
| `python -m unittest discover -s simulator -v` | 6 testes executados; todos passaram (`OK`). Cobrem leitura válida, valor mais recente, falha simulada separada de erro da aplicação, rejeição de leitura inválida sem incrementar o contador válido, gauge de processamento zerado após sucesso/erro, configuração e janelas do pico. |
| `docker build -t mecaniqa-simulator:metrics-v1 ./simulator` | Build concluído com a imagem base `python:3.13-slim` e dependências fixadas. |
| Execução isolada, `PEAK_MODE=off`, consulta de `/metrics` | Contadores válidos aumentaram de 9 para 15 entre duas consultas; `iot_peak_active` permaneceu 0. |
| Execução isolada, `PEAK_MODE=always` | `/metrics` expôs leitura válida, `iot_peak_active=1` e taxa alvo 10/s para taxa normal 2/s e multiplicador 5. |
| SIGTERM e usuário da imagem | `docker stop` encerrou o processo com saída 0 e log `Simulator stopped`; a imagem executa como `10001:10001`. |
| `promtool check config` na configuração extraída do ConfigMap | `SUCCESS: /tmp/prometheus.yml is valid prometheus config file syntax`. |
| Parse YAML local | PyYAML carregou os seis recursos: Deployment/Service do simulador, ConfigMap/PVC/Deployment/Service do Prometheus. |
| Coleta Prometheus em contêineres Docker | Na mesma rede Docker, com alias `simulator.mecaniqa.svc.cluster.local` usado pelo manifesto: `up{job="iot-simulator"}=1`, `sum(iot_readings_total)=35` e `sum(rate(iot_readings_total[1m]))=0.474620050659912`. Aguardar 40 segundos permitiu obter amostras para a taxa. |
| Sintaxe de `scripts/deploy-local.ps1` e `git diff --check` | Parse do PowerShell sem erros e verificação de whitespace sem erros. |

A coleta Prometheus acima comprova o funcionamento do exporter e do scrape
entre contêineres Docker locais. Ela não é uma execução no cluster Kubernetes.

## Verificações pendentes — ambiente Kubernetes indisponível

O kubeconfig esperado em `.local/kubeconfig` não existe, `kubectl config
get-contexts` não lista contextos e `kubectl --context kind-mecaniqa apply
--dry-run=server -f k8s/` retornou `context "kind-mecaniqa" does not exist`.
Também não há `.local/bin/kind.exe` no workspace. Portanto, nesta execução não
foi possível:

- executar o dry-run contra o servidor Kubernetes;
- carregar a imagem no nó Kind ou executar `scripts/deploy-local.ps1`;
- confirmar Pods, Services, PVC Bound ou logs/eventos do cluster;
- fazer port-forward do Service Prometheus no Kubernetes ou confirmar as
  consultas no Prometheus implantado no namespace `mecaniqa`.

Não foram feitas alterações para contornar a falta de contexto ou do cluster.
Para concluir essas verificações, disponibilize o Kind `mecaniqa`, o binário
Kind em `.local/bin/kind.exe` e um kubeconfig `.local/kubeconfig` contendo o
contexto `kind-mecaniqa`; então execute o fluxo descrito em
[projeto-metricas.md](./projeto-metricas.md).

## Limites da evidência

Os resultados comprovam instrumentação e coleta de carga sintética em uma
execução local, não a integração implantada no Kubernetes nem capacidade para
milhares de sensores reais simultâneos. A configuração Kubernetes declara uma
réplica do simulador e coleta estática pelo Service, sem descoberta individual
de Pods adicionais.
