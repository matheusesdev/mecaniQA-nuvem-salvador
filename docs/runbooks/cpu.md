# Runbook de CPU do simulador

## Disparo e impacto

`mecaniqa-alert-cpu` dispara quando a maior CPU do processo Python entre as réplicas ultrapassa 80% do limite de 250m por dois minutos. Isso equivale a mais de 200m; o HPA age antes, a 70% do request de 50m.

Saturação pode reduzir o processamento, aumentar atrasos e levar o HPA ao máximo de cinco Pods. O dashboard CPU apresenta porcentagem de um núcleo somada entre réplicas, unidade diferente do alarme.

## Preparação e responsáveis

Piloto Juan Pablo conduz o diagnóstico; copiloto Matheus executa e confere; QA Rafael valida o resultado; Scrum Master Albert coordena o registro. Abrir incidente com horário UTC, impacto, última mudança e condição do alarme. Confirmar se há teste acadêmico autorizado em andamento antes de interpretar a injeção como defeito real.

Na raiz do projeto, em PowerShell:

```powershell
$env:KUBECONFIG = Join-Path (Get-Location) '.local/kubeconfig'
kubectl --context kind-mecaniqa -n mecaniqa get hpa,pods,deploy
kubectl --context kind-mecaniqa -n mecaniqa top pods
kubectl --context kind-mecaniqa -n mecaniqa describe hpa simulator
kubectl --context kind-mecaniqa -n mecaniqa get events --sort-by=.lastTimestamp
kubectl --context kind-mecaniqa -n mecaniqa logs -l app=simulator --prefix --tail=100
curl.exe --fail --max-time 5 http://localhost:18080/health
```

A API precisa retornar status UP, mysql UP e redis UP. Ela é um serviço separado do simulador, portanto sua saúde não encerra sozinha o alarme do simulador. Se top falhar, conferir a infraestrutura de métricas antes de concluir que o uso de recursos está baixo:

```powershell
kubectl --context kind-mecaniqa get apiservice v1beta1.metrics.k8s.io
kubectl --context kind-mecaniqa -n kube-system logs deployment/metrics-server --tail=100
```

Manter port-forward de Prometheus em outro terminal e abrir http://localhost:9090 para executar as consultas abaixo. Conferir `up{job="iot-simulator"}` igual a 1 para cada target; falha de coleta é NoData, não recuperação. A lista de targets deve acompanhar as réplicas prontas após a atualização de DNS. O Grafana em http://localhost:3000/alerting/list apresenta os estados das quatro regras.

## Diagnóstico específico

```promql
100 * max(rate(process_cpu_seconds_total{job="iot-simulator"}[1m])) / 0.25
```

Comparar com top pods e condições ScalingActive, AbleToScale e ScalingLimited do HPA. Se faltar métrica, investigar Metrics Server; se Pods estiverem Pending, usar describe pod com o nome listado e verificar CPU disponível no nó. CPU do processo e CPU do contêiner podem diferir. Inspecionar STRESS_CPU_MS e READINGS_PER_SECOND no Deployment. Se não houver teste, procurar mudança de algoritmo ou carga e correlacionar com sucesso e erros.

## Recuperação

Suspender a injeção conforme abaixo. Em tráfego real, reduzir a origem de carga identificada ou corrigir o processamento. Se o HPA já está em cinco réplicas, o limite foi atingido; avaliar capacidade antes de alterar o máximo, preservando a decisão acadêmica 1 a 5.

Se o incidente for causado pelo teste controlado e sua coleta já estiver concluída, interromper a injeção restaurando a configuração normal. O script de teste faz essa restauração automaticamente no finally. Se ele foi interrompido abruptamente, execute:

```powershell
kubectl --context kind-mecaniqa -n mecaniqa set env deployment/simulator STRESS_CPU_MS- STRESS_MEMORY_MIB- STRESS_ERROR_RATIO- READINGS_PER_SECOND=1 PEAK_MODE=scheduled
kubectl --context kind-mecaniqa -n mecaniqa rollout status deployment/simulator --timeout=180s
```

Esses valores são os padrões versionados do laboratório. Se existia outra configuração antes do teste, restaurar os valores registrados no início do incidente. Não aumentar limites sem verificar capacidade do nó e efeito nos alarmes; não remover PVCs ou dados. Se uma versão nova causou a regressão, comparar o histórico antes de aprovar uma reversão:

```powershell
kubectl --context kind-mecaniqa -n mecaniqa rollout history deployment/simulator
```

Registrar a versão estável selecionada antes de executar `kubectl --context kind-mecaniqa -n mecaniqa rollout undo deployment/simulator --to-revision=<revisao-validada>`. O marcador deve ser substituído pela revisão conferida; não executar uma reversão cega que possa reativar carga de teste.

## Encerramento e evidências

Aguardar a janela de taxa de 1 minuto e a avaliação do Grafana a cada 20 s. Confirmar a regra inactive, targets saudáveis e métricas abaixo da condição de disparo durante pelo menos cinco minutos. Quando a carga voltar ao normal, aguardar a estabilização de redução de 300 s do HPA e verificar a volta a uma réplica pronta. Não forçar scale manual enquanto o HPA controla o Deployment.

Registrar valores antes e depois, horários, ações, logs, eventos, contagem de réplicas e captura da regra e do dashboard correspondente. Conferir cinco verificações consecutivas bem-sucedidas da API, reinícios estáveis e ausência de outras regras firing. Se a recuperação ultrapassar 30 minutos, registrar violação do RTO e escalar ao coordenador. O desaparecimento da série ou um erro na consulta não atende ao encerramento.

Referência: [acordo operacional](../acordo-operacional.md). Evidências do exercício: [teste de estresse](../evidencias/2026-10-21-estresse/).
