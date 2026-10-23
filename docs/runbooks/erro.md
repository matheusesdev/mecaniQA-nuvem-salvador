# Runbook de Erros de processamento

## Disparo e impacto

`mecaniqa-alert-erro` dispara quando rejeições / tentativas supera 5%, com ao menos vinte tentativas na janela de 1 minuto, e a condição persiste por dois minutos.

Leituras inválidas são rejeitadas; isso reduz os dados processados. Uma falha de temperatura ou elétrica validamente recebida conta como sucesso e como falha do sensor, não como erro de processamento.

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
sum(rate(iot_processing_errors_total{job="iot-simulator"}[1m])) / (sum(rate(iot_processing_errors_total{job="iot-simulator"}[1m])) + sum(rate(iot_readings_total{job="iot-simulator"}[1m])))
```

```promql
sum(increase(iot_processing_errors_total{job="iot-simulator"}[1m])) + sum(increase(iot_readings_total{job="iot-simulator"}[1m]))
```

Conferir as mensagens Rejected sensor reading e os tipos aceitos: temperature/electrical, value numérico finito e fault booleano. Verificar STRESS_ERROR_RATIO e mudanças no gerador. Uma proporção sem tentativas é indefinida; não classificar como sucesso ou erro zero. Evitar salvar dados identificáveis de dispositivos em evidências.

## Recuperação

Encerrar a injeção de erros conforme abaixo. Fora do exercício, corrigir a origem do payload ou reverter a mudança comprovadamente defeituosa. Manter a validação de entradas ativa; não aceitar dados inválidos para reduzir a taxa de erros. Reprocessamento só se houver uma fonte durável comprovada, inexistente no gerador atual.

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
