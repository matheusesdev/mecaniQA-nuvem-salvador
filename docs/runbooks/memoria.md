# Runbook de Memória do simulador

## Disparo e impacto

`mecaniqa-alert-memoria` dispara quando o maior RSS por réplica ultrapassa 102,4 MiB por dois minutos, equivalente a 80% do limite de 128Mi.

A margem até o limite pode se esgotar e causar OOMKilled. O HPA usa memória do contêiner relativa ao request de 64Mi, diferente do RSS do processo.

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
max(process_resident_memory_bytes{job="iot-simulator"}) / 1024 / 1024
```

Comparar com top pods, reinícios e o campo Last State de describe pod. Se houver OOMKilled, salvar logs --previous do Pod identificado antes da recuperação. Verificar STRESS_MEMORY_MIB no Deployment e se o crescimento continua sem carga. Alocação por réplica aumenta o consumo total quando o HPA escala; verificar também a pressão de memória no nó.

## Recuperação

Remover a alocação controlada conforme abaixo. Em vazamento real, preservar diagnóstico e reverter a versão identificada ou corrigir a retenção. Reiniciar um Pod pode aliviar temporariamente o uso, mas não corrige a causa; registrar a hipótese antes de reiniciar. Não elevar o limite para esconder o alarme.

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
